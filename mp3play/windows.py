import random

from ctypes import windll, c_buffer, create_unicode_buffer

class _mci:
	def __init__(self):
		# self.w32mci = windll.winmm.mciSendStringA
		self.w32mci = windll.winmm.mciSendStringW
		# self.w32mcierror = windll.winmm.mciGetErrorStringA
		self.w32mcierror = windll.winmm.mciGetErrorStringW

	def send(self, command: str):
		# buffer = c_buffer(255)
		buffer = create_unicode_buffer(255)
		errorcode = self.w32mci(str(command), buffer, 254, 0)
		if errorcode:
			return errorcode, self.get_error(errorcode)
		else:
			return errorcode, buffer.value

	def get_error(self, error):
		error = int(error)
		# buffer = c_buffer(255)
		buffer = create_unicode_buffer(255)
		self.w32mcierror(error, buffer, 254)
		return buffer.value

	def directsend(self, txt: str):
		(err, buf) = self.send(txt)
		# print('Error %s for "%s": %s' % (str(err), txt, buf))
		if err != 0:
			print('Error %s for "%s": %s' % (str(err), txt, buf))
		return (err, buf)

# TODO: detect errors in all mci calls
class AudioClip:
	def __init__(self, filename: str):
		# filename = filename.replace('/', '\\')
		self.filename: str = filename
		self._alias: str = 'mp3_%s' % str(random.random())

		self._mci: _mci = _mci()

		_ = self._mci.directsend('open "%s" alias %s' % (filename, self._alias ))
		# self._mci.directsend('open "%s" type mpegvideo alias %s' % (filename, self._alias ))
		_ = self._mci.directsend('set %s time format milliseconds' % self._alias)

		_, buf = self._mci.directsend('status %s length' % self._alias)
		self._length_ms: int = int(buf)

	def volume(self, level: int):
		"""Sets the volume between 0 and 100."""
		_ = self._mci.directsend('setaudio %s volume to %d' %
				(self._alias, level * 10) )

	def play(self, start_ms: int | None = None, end_ms: int | None = None):
		start_ms = 0 if not start_ms else start_ms
		end_ms = self.milliseconds() if not end_ms else end_ms
		# err, buf = self._mci.directsend('play %s from %d to %d' %(self._alias, start_ms, end_ms))
		_ = self._mci.directsend('play %s repeat' %self._alias)

	def isplaying(self):
		return self._mode() == 'playing'

	def _mode(self):
		_, buf = self._mci.directsend('status %s mode' % self._alias)
		return str(buf)

	def pause(self):
		_ = self._mci.directsend('pause %s' % self._alias)

	def unpause(self):
		_ = self._mci.directsend('resume %s' % self._alias)

	def ispaused(self):
		return self._mode() == 'paused'

	def stop(self):
		_ = self._mci.directsend('stop %s' % self._alias)
		_ = self._mci.directsend('seek %s to start' % self._alias)

	def milliseconds(self):
		return self._length_ms

	# TODO: this closes the file even if we're still playing.
	# no good.  detect isplaying(), and don't die till then!
	def __del__(self):
		_ = self._mci.directsend('close %s' % self._alias)
