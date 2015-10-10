Title: Stopping blocking threads in Python using gevent (sort of)
Date: 2015-08-20 15:43

**tl;dr: The [gist here](https://gist.github.com/mikeanthonywild/4e4784f1974d21f366d5) provides a replacement `threading.Thread` class with a `stop()` method using Gevent and greenlets. It should also be prefixed by saying these aren't proper 'threads', but 'greenlets'.**

Something which crops up [time](http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python) and [time again](http://stackoverflow.com/questions/5019436/python-how-to-terminate-a-blocking-thread), is how to stop a blocking thread in Python. Take the following example to spawn a blocking thread in the background:

    :::python
    import threading
    import time


    t = threading.Thread(target=time.sleep, args=[10])
    t.start()
    print("Waiting 10s to exit...")
    print("Press <Ctrl-C> to stop thread")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            exit("Keyboard interrupt - waiting for thread to finish...")

Output:

    :::console
    Waiting 10s to exit...
    Press <Ctrl-C> to stop thread
    ^C
    Keyboard interrupt - waiting for thread to finish...
    [...]

Notice that even though we catch the `^C` escape sequence, the main thread won't exit until the sleep thread has finished, even if you mash `^C`. A quick fix in this case would be to set the `t.daemon ` property to `True` before the thread is started, meaning that the main thread won't wait for child threads to finish before exiting. This is fine for trivial examples like the one above, but can become a real issue when we start dealing with sockets and the like. 

Here's a more realistic example:

    :::python
    import threading
    import socket
    import time


    class StoppableThread(threading.Thread):
        def run(self):
            s = socket.socket()
            s.bind(('127.0.0.1', 0))
            s.listen(1)
            print("Listening on {}:{}".format(s.getsockname()[0], s.getsockname()[1]))

            conn, addr = s.accept()

    if __name__ == '__main__':
        t = StoppableThread()
        t.start()
        print("Press <Ctrl-C> to stop thread")
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                exit("Keyboard interrupt - waiting for thread to finish...")

Output:

    :::console
    Press <Ctrl-C> to stop thread
    Listening on 127.0.0.1:65309
    ^C
    Keyboard interrupt - waiting for thread to finish...
    [...]

Using `t.daemon = True` on a socket server thread can lead to the socket not being released – thus it's impossible to restart the server as Python won't be able to bind to the port you were using (ignoring the `SO_REUSEADDR` flag). Additionally, sometimes Python can't kill its child threads and you end up having to force-kill the entire process, leading to the afformentioned issue. Yet, if we use `t.daemon = False`, we have to kill the whole process anyway, because it's blocked by `s.accept()` until something connects. 

### Solution

The widely-accepted solution is to set a timeout on our blocking functions so we can periodically check a `threading.Event` which we set from the main thread to indicate we want the child thread to stop. Unfortunately this solution is a little clunky:

    :::python
    class StoppableThread(threading.Thread):
        def __init__(self):
            super(StoppableThread, self).__init__()
            self._stop = threading.Event()

        def run(self):
            s = socket.socket()
            s.settimeout(1)             # Socket will raise exception if nothing received
            s.bind(('127.0.0.1', 0))
            s.listen(1)
            print("Listening on {}:{}".format(s.getsockname()[0], s.getsockname()[1]))

            while True:
                try:
                    conn, addr = s.accept()
                except socket.error:
                    # Check for stop signal
                    if self._stop.is_set():
                        print("Shutting down cleanly...")
                        s.close()
                        return
                    
Now when we catch a `KeyboardInterrupt` we can trigger the server thread to stop:

    :::python
    except KeyboardInterrupt:
        t._stop.set()
        exit("Keyboard interrupt - waiting for thread to finish...")

### A better solution using Gevent and greenlets

The official description of a greenlet is rather confusing given the context of this post, so a simple example will be used to explain it instead (taken from http://sdiehl.github.io/gevent-tutorial/):

    :::python
    import time
    import gevent
    from gevent import select

    start = time.time()
    tic = lambda: 'at %1.1f seconds' % (time.time() - start)

    def gr1():
        # Busy waits for a second, but we don't want to stick around...
        print('Started Polling: %s' % tic())
        select.select([], [], [], 2)
        print('Ended Polling: %s' % tic())

    def gr2():
        # Busy waits for a second, but we don't want to stick around...
        print('Started Polling: %s' % tic())
        select.select([], [], [], 2)
        print('Ended Polling: %s' % tic())

    def gr3():
        print("Hey lets do some stuff while the greenlets poll, %s" % tic())
        gevent.sleep(1)

    gevent.joinall([
        gevent.spawn(gr1),
        gevent.spawn(gr2),
        gevent.spawn(gr3),
    ])

Output:

    :::console
    Started Polling: at 0.0 seconds
    Started Polling: at 0.0 seconds
    Hey lets do some stuff while the greenlets poll, at 0.0 seconds
    Ended Polling: at 2.0 seconds
    Ended Polling: at 2.0 seconds

What this shows is that Gevent provides pseudo-concurrency by context switching on blocking functions like `select()`. The keen-eyed observer will notice that the snippet above uses a special `gevent.select`, a version of the standard Python implementation which has been [monkeypatched](http://stackoverflow.com/questions/5626193/what-is-a-monkey-patch) to behave co-operatively to allow the switching behaviour seen above. It's also possible to just import a standard blocking Python module and patch it at runtime like so:

    :::python
    import time

    from gevent import monkey
    monkey.patch_all()

    time.sleep(1)   # Now it can be used inside a greenlet!

This is significant, because without the monkeypatching, it wouldn't be possible to implement a stoppable thread as easily. Critically, Gevent also provides a `Greenlet.kill()` method, which stops the greenlet from executing.

#### Putting everything together

We can put all of this together to obtain our stoppable thread:

1. Use `gevent.spawn()` to spawn a new greenlet with the thread's `run()` method.
2. Call the greenlet's `kill()` method to stop the 'thread'.
3. Release all the resources used by the greenlet.

An example stoppable thread class is presented here:

    :::python
    """ betterthreads provides an enhanced replacement for the 
        threading.Thread class geared towards cleanly stopping blocking
        threads.
    """

    import gevent
    import uuid

    from gevent.event import Event


    # Helper to generate new thread names
    _counter = 0
    def _newname(template="Thread-%d"):
        global _counter
        _counter = _counter + 1
        return template % _counter


    class Thread(object):
        """ An enhanced replacement for the Python 
        :class:`threading.Thread` class.

        This isn't actually a true thread, instead it uses Gevent to
        implement co-routines. Using :func:`gevent.monkey.patch_all`, all
        Python blocking functions are replaced with non-blocking Gevent
        alternatives which allow 
        """

        __initialized = False

        def __init__(self, group=None, name=None):
            """ Thread constructor

            :param group: should be ``None``; reserved for future 
            extension when a :class:`ThreadGroup` class is implemented.
            :param name: the thread name.  By default, a unique name
            is constructed of the form "Thread-*N*" where *N* is a small 
            decimal number.

            If the subclass overrides the constructor, it must make sure 
            to invoke the base class constructor (``Thread.__init__()``) 
            before doing anything else to the thread.
            """

            # WARNING: Not sure about the side-effects of this...
            # Monkeypatch a bunch of blocking and thread-related
            # constructs to use gevent alternatives. Threads are now
            # co-routines which yield to each other when a Gevent
            # blocking operation is called.
            from gevent import monkey
            monkey.patch_all()

            self.__name = str(name or _newname())
            self.__ident = None
            self.__started = Event()
            self.__stopped = False
            self.__initialized = True

        def start(self):
            """ Start the thread's activity.

            It must be called at most once per thread object.  It
            arranges for the object's :meth:`run` method to be invoked in
            a separate thread of control.

            This method will raise a :exc:`RuntimeError` if called more 
            than once on the same thread object.
            """
            if not self.__initialized:
                raise RuntimeError("thread.__init__() not called")
            if self.__started.is_set():
                raise RuntimeError("thread already started")

            self._bootstrap()

        def _bootstrap(self):
            self.__ident = uuid.uuid4()
            self.__started.set()
            self._g_main = gevent.spawn(self.run)

        def stop(self, blocking=False):
            """ Stop the thread's activity. 

            :param blocking: block until thread has stopped completely.
            """
            if self.__stopped:
                raise RuntimeError("threads can only be stopped once")

            self.__stopped = True
            self._g_main.kill()
            self.shutdown()
            if blocking:
                self._g_main.join()

        def run(self):
            """ Method representing the thread's activity. 

            You may override this method in a subclass.
            """
            pass

        def join(self, timeout=None):
            """ Wait until the thread terminates. 

            This blocks the calling thread until the
            thread whose :meth:`join` method is called terminates -- 
            either normally or through an unhandled exception -- or until
            the optional timeout occurs.

            When the *timeout* argument is present and not ``None``, it 
            should be a floating point number specifying a timeout for 
            the operation in seconds (or fractions thereof). As 
            :meth:`join` always returns ``None``, you must call 
            :meth:`isAlive` after :meth:`join` to decide whether a 
            timeout happened -- if the thread is still alive, the 
            :meth:`join` call timed out.

            When the *timeout* argument is not present or ``None``, the 
            operation will block until the thread terminates.

            A thread can be :meth:`join`\ ed many times.

            :meth:`join` raises a :exc:`RuntimeError` if an attempt is 
            made to join the current thread as that would cause a 
            deadlock. It is also an error to :meth:`join` a thread before
            it has been started and attempts to do so raises the same exception.
            """
            if not self.__initialized:
                raise RuntimeError("Thread.__init__() not called")
            if not self.__started.is_set():
                raise RuntimeError("cannot join thread before it is started")
            
            self._g_main.join(timeout)

        def shutdown(self):
            """ Cleanup method called when thread is stopping.

            This method is run when the thread is stopped. Any resources
            used by the thread (sockets and such) should be safely closed
            here.

            You may override this method in a subclass.
            """
            pass

        def __repr__(self):
            assert self.__initialized, "Thread.__init__() was not called"
            status = "initial"
            if self.__started.is_set():
                status = "started"
            if self.__stopped:
                status = "stopped"
            if self.__ident is not None:
                status += " %s" % self.__ident
            return "<%s(%s, %s)>" % (self.__class__.__name__, self.__name, status)

        def __enter__(self):
            return self

        def __exit__(self):
            self.stop()

        @property
        def name(self):
            assert self.__initialized, "Thread.__init__() not called"
            return self.__name

        @name.setter
        def name(self, name):
            assert self.__initialized, "Thread.__init__() not called"
            self.__name = str(name)

        @property
        def ident(self):
            assert self.__initialized, "Thread.__init__() not called"
            return self.__ident

        def isAlive(self):
            assert self.__initialized, "Thread.__init__() not called"
            return self.__started.is_set() and not self.__stopped

        is_alive = isAlive

        def getName(self):
            return self.name

        def setName(self, name):
            self.name = name

Why use greenlets when we can just implement timeouts and poll our stop flag, as above? Because it's possible to get a stoppable thread using one line of code, instead of implementing timeouts etc. Simple changing `class StoppableThread(threading.Thread):` to `class StoppableThread(betterthreads.Thread):` does the trick:

    :::python
    import betterthreads
    import socket
    import time


    class StoppableThread(betterthreads.Thread):
        def run(self):
            s = socket.socket()
            s.bind(('127.0.0.1', 0))
            s.listen(1)
            print("Listening on {}:{}".format(s.getsockname()[0], s.getsockname()[1]))

            conn, addr = s.accept()

        def shutdown()
            print("Shutting down cleanly...")
            conn.close()
            s.close()


    if __name__ == '__main__':
        t = StoppableThread()
        t.start()
        print("Press <Ctrl-C> to stop thread")
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                exit("Keyboard interrupt - waiting for thread to finish...")

Output:

    :::console
    Press <Ctrl-C> to stop thread
    Listening on 127.0.0.1:65309
    ^C
    Keyboard interrupt - waiting for thread to finish...
    Shutting down cleanly...
    
    $

`betterthreads.Thread` implements the same interface as `threading.Thread`, so it should be a drop-in replacement.
