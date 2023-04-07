
import signal
import sys
import time

from insaflu_upload.manager import MainInsaflu


def signal_handler(signal, frame):
    print("exiting")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main_insaflu = MainInsaflu()
    main_insaflu.run()
