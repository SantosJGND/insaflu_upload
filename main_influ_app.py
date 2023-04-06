
import signal
import sys
import threading
import time
from _thread import interrupt_main
from threading import Event, Thread

from main_influ_app_test import generate_processors


class LockWithOwner:

    lock = threading.RLock()
    owner = 'A'

    def acquire_for(self, owner):
        n = 0
        while True:
            self.lock.acquire()
            if self.owner == owner:
                break
            n += 1
            self.lock.release()
            time.sleep(0.001)
        print("------------------")
        print('lock acquired')

    def release_to(self, new_owner):
        self.owner = new_owner
        self.lock.release()


class InsafluFileProcessThread(Thread):
    def __init__(self, compressor, thread_lock: LockWithOwner):
        super(InsafluFileProcessThread, self).__init__()
        self.lock = thread_lock
        self.compressor = compressor
        self._stopevent = Event()  # initialize the event

    def run(self):
        try:
            while True:
                self._stopevent.clear()  # Make sure the thread is unset
                self.lock.acquire_for("A")

                self.compressor.run()
                lock.release_to('B')

        except Exception as e:
            print(e)
            interrupt_main()

    def stop(self):
        self._stopevent.set()

    def join(self, timeout=None):
        self._stopevent.set()
        Thread.join(self, timeout)


class TelevirFileProcessThread(Thread):
    def __init__(self, processor, thread_lock: LockWithOwner):
        super(TelevirFileProcessThread, self).__init__()
        self.lock = thread_lock
        self.processor = processor
        self._stopevent = Event()  # initialize the event
        self.work_period = processor.real_sleep
        print("work period: {} s".format(self.work_period))

    def run(self):
        try:
            while True:
                self._stopevent.clear()  # Make sure the thread is unset
                self.lock.acquire_for("B")
                start_time = time.time()
                execution_time = 0

                while execution_time < self.work_period:
                    self.processor.run()
                    execution_time = time.time() - start_time
                    time.sleep(30)

                lock.release_to('A')

        except Exception as e:
            print(e)
            interrupt_main()

    def stop(self):
        self._stopevent.set()

    def join(self, timeout=None):
        self._stopevent.set()
        Thread.join(self, timeout)


def signal_handler(signal, frame):
    print("exiting")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    file_processor, televir_processor = generate_processors()

    lock = LockWithOwner()
    lock.owner = 'A'

    file_processor_task = InsafluFileProcessThread(
        file_processor, lock
    )
    televir_processor_task = TelevirFileProcessThread(
        televir_processor, lock
    )

    file_processor_task.daemon = True
    televir_processor_task.daemon = True

    file_processor_task.start()
    televir_processor_task.start()

    while True:
        pass
