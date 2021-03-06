import time

from multiprocessing import Process, Pipe

from rq.timeouts import JobTimeoutException

from .util import get_args

from pyvotune.log import logger
log = logger()


def rq_runner(candidates, args):
    log.debug("Runner process called")
    timeout_val = args.setdefault('rq_timeout_fitness', 0)

    try:
        rq_timeout = args['rq_timeout']

        pickled_args = get_args(args)

        parent_conn, child_conn = Pipe()

        proc = Process(
            target=_child_runner, args=(child_conn, candidates, get_args(args)))

        try:
            proc.start()

            res = parent_conn.poll(rq_timeout)

            if res is None:
                log.debug("Timed out waiting for child result")
                proc.terminate()

                raise

            else:
                data = parent_conn.recv()
                #log.debug("Received from child {0}".format(data))

                proc.join(rq_timeout)

                return data[0]

        except JobTimeoutException as e:
            log.exception("Runner timed out {0}".format(e))
            proc.terminate()
            raise

    except Exception as e:
        log.exception("Excepted in rq runner {0} {1}".format(type(e), e))
        return timeout_val


def _child_runner(child_conn, candidates, args):
    try:
        evaluator = args['rq_evaluator']

        res = evaluator(candidates, args)
    except Exception as e:
        log.exception("Excepted in child {0}".format(e))
        res = args['rq_timeout_fitness']

    child_conn.send(res)
    child_conn.close()
