from array import array
from struct import pack

import tempfile
import pyaudio
import sys
import wave
import os


THRESHOLD = 2000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
SILENCE_DURATION = 40 # end recording after period of silence reaches this value
WAIT_DURATION = 500 # end recording if no input before this value is reached
SPEECH_DURATION = 300 # end recording if too much input

class Microphone:
	"""
	Control all aspects of recording and receiving input 
	from the microphone.
	
	"""
	def __init__(self):
		self.recordedWavFilename = ""

	def listen(self):
		"""Record speech and store in a temporary file."""
		(_, rec_wav_filename) = tempfile.mkstemp('.wav')

		sample_width, data = self.record()
		s_data = data[:]
		data = pack('<' + ('h'*len(data)), *data)
		wf = wave.open(rec_wav_filename, 'wb')
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(sample_width)
		wf.setframerate(RATE)
		wf.writeframes(b''.join(data))
		wf.close()

		self.recordedWavFilename = rec_wav_filename
		return self.recordedWavFilename,s_data

	def rate(self):
		"""Return recording rate."""
		return RATE

	def filename(self):
		"""Return temp file storing speech recording."""
		return self.recordedWavFilename

	def housekeeping(self):
		"""Delete temp file when it is no longer needed."""
		os.remove(self.recordedWavFilename)

	def is_silent(self, sound_data):
		"""Check if speech volume is below silence threshold."""
		return max(sound_data) < THRESHOLD

	def add_silence(self, sound_data, seconds):
		"""Pad end of speech recording with silence."""
		r = array('h', [0 for i in xrange(int(seconds*RATE))])
		r.extend(sound_data)
		r.extend([0 for i in xrange(int(seconds*RATE))])
		return r

	def record(self):
		"""Open pyaudio stream and record audio from mic."""
		p = pyaudio.PyAudio()
		stream = p.open(format = FORMAT,
						channels = CHANNELS, 
						rate = RATE, 
						input = True, 
						frames_per_buffer = CHUNK)
		print("Listening...")

		speech_started = False
		speech = 0
		silence_before_speech = 0
		silence_after_speech = 0
		r = array('h')

		while 1:
			sound_data = array('h', stream.read(CHUNK))
			if sys.byteorder == 'big':
				sound_data.byteswap()
			r.extend(sound_data)

			silent = self.is_silent(sound_data)

			if speech_started:
				if silent:
					silence_after_speech += 1
				elif not silent:
					silence_after_speech = 0
					speech += 1

				# break after a period of silence
				if silence_after_speech > SILENCE_DURATION:
					break
				# break after too much input
				if speech > SPEECH_DURATION:
					break
			else: 
				if silent:
					silence_before_speech += 1
				elif not silent: 
					speech_started = True
				# break if no input
				if silence_before_speech > WAIT_DURATION:
					#print("Warning: no input. Increase the volume on your mic.")
					break

		print("Processing...")

		sample_width = p.get_sample_size(FORMAT)
		stream.stop_stream() 
		stream.close()
		p.terminate()

		r = self.add_silence(r, 0.5)
		return sample_width, r
