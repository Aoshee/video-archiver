from youtube_dl import YoutubeDL

import multiprocessing
import datetime
import sys


class OutputWriter(object):
    """
    Wrapper around a multiprocessing.Queue that can act like a write-only file object

    Used to capture stdout/stderr of child downloader and send data back to parent
    """
    def __init__(self):
        self.q = multiprocessing.Queue()

    def write(self, msg):
        self.q.put(msg)
        pass

    def isatty(self):
        return False

    def flush(self):
        return


class Downloader(object):
    """
    Downloader which manages the actual download process
    """
    def __init__(self, dl_id, url):
        self.dl_id = dl_id
        self.url = url

        self.start_time = datetime.datetime.utcnow()


        self.download_proc = None

        self.status_queue = multiprocessing.Queue()
        self.status = {}

        self.child_output = OutputWriter()
        self.log = ""


        info_downloader = YoutubeDL({'quiet': True})
        info_downloader.add_default_info_extractors()

        self.info = info_downloader.extract_info(self.url, download=False)

    def start(self):
        if self.download_proc is None:
            self.status_queue = multiprocessing.Queue()

            self.child_output = OutputWriter()

            self.download_proc = DownloadProcess(self.url, self.status_queue, self.child_output)
            self.download_proc.start()

            self.log += '### Download process started at {} ###\n'.format(datetime.datetime.utcnow())


    def stop(self):
        if self.download_proc is not None:
            self.download_proc.stop()
            self._update_log()
            self.log += '### Download process stopped at {} ###\n'.format(datetime.datetime.utcnow())
            self.download_proc = None

    def _update_log(self):
        while not self.child_output.q.empty():
            self.log += self.child_output.q.get() + '\n'

    def get_log(self):
        self._update_log()
        return self.log

    def _update_status(self):
        while not self.status_queue.empty():
            self.status = self.status_queue.get()

    def get_title(self):
        type = self.info.get('_type', 'video').title()
        return '{}: {}'.format(type, self.info['title'])

    def get_state(self):
        self._update_status()
        return self.status.get('status', 'paused').title()

    def get_progress_percent(self):
        self._update_status()
        if self.status.get('total_bytes') and self.status.get('downloaded_bytes') is not None:
            return 100 * self.status.get('downloaded_bytes') / self.status.get('total_bytes')
        return 0

    def get_size(self):
        self._update_status()
        return self.status.get('downloaded_bytes', 'unk')

    def get_total_size(self):
        self._update_status()
        if 'total_bytes' in self.status:
            return self.status['total_bytes']
        elif 'total_bytes_estimate' in self.status:
            return self.status['total_bytes_estimate']
        else:
            return 'unk'

    def get_elapsed_time(self):
        self._update_status()
        return round(self.status.get('elapsed', 0), 2)


    def get_stats(self):
        return {'elapsed_time': self.get_elapsed_time(), 'downloaded_bytes': self.get_size(), 'total_bytes': self.get_total_size(), 'percent_done': self.get_progress_percent()}


class DownloadProcess(multiprocessing.Process):
    """
    Actual download process which calls youtube-dl. You should never need to interact with this directly.
    """
    def __init__(self, url, status_queue, output_writer):
        super(DownloadProcess, self).__init__()

        self.url = url
        self.status_queue = status_queue

        self.info = {}

        sys.stdout = output_writer
        sys.stderr = output_writer

        self.downloader = YoutubeDL({'progress_hooks': [self.update_status]})
        self.downloader.add_default_info_extractors()

    def update_status(self, status):
        self.status_queue.put(status)

    def run(self):
        self.info = self.downloader.extract_info(self.url)

    def stop(self):
        # Kill any child processes that may have spawned (e.g. ffmpeg)
        import psutil, signal

        s = psutil.Process()
        for child in s.children(recursive=True):
            child.send_signal(signal.SIGINT)