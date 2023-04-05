
import signal
import sys
from _thread import interrupt_main
from threading import Event, Thread

from main_influ_app_test import generate_processors


class InsafluFileProcessThread(Thread):
    def __init__(self, compressor):
        super(InsafluFileProcessThread, self).__init__()
        self.compressor = compressor
        self._stopevent = Event()  # initialize the event
        self._sleepperiod = 1.0  # we wait 1 second to start the thread

    def run(self):
        try:
            self._stopevent.clear()  # Make sure the thread is unset

            while not self._stopevent.is_set():
                self.compressor.run()
                # interrupt_main()  # stop the main thread

        except Exception as e:
            print(e)

    def stop(self):
        self._stopevent.set()

    def join(self, timeout=None):
        # set the stop event so the training loop is terminated.
        self._stopevent.set()
        Thread.join(self, timeout)
