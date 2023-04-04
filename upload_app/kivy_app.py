import json
import threading
import time
from threading import Event, Thread

from insaflu_upload.insaflu_upload import InsafluPreMain
from main_utils import generate_compressor


class CreateTrainModelPeriodicallyThread(Thread):
    def __init__(self, table_name):
        super(CreateTrainModelPeriodicallyThread, self).__init__()
        self.table_name = table_name
        self._stopevent = Event()  # initialize the event
        self._sleepperiod = 1.0  # we wait 1 second to start the thread

    def run(self):
        try:
            self._stopevent.clear()  # Make sure the thread is unset
            mydb = mysql.connector.connect(database_config)
            conn = mydb.cursor()
            while not self._stopevent.is_set():
                time.sleep(5 * 60)  # train the model every 5 minutes
                model = json.load(model_path)
                data = (mysql
                        .connector
                        .connect(database_config)
                        .cursor()
                        .execute("SELECT * FROM {}".format(table_name)))
                model.train(data)
                json.save(model, model_path)
                self._stopevent.wait(self._sleepperiod)
            mydb.commit()
            conn.close()
            mydb.close()
        except Exception as e:
            print(e)

    def join(self, timeout=None):
        # set the stop event so the training loop is terminated.
        self._stopevent.set()
        Thread.join(self, timeout)
