import time,fcntl,exceptions,os

try:
  import codecs
except:
  # We're in non-modern environment
  codecs = None

SLEEP_TIME=0.1 # Time to sleep between each try
TRIES=10 # number of tries

METHOD='dotfile' 
# METHOD='fcntl'

import warnings
warnings.filterwarnings('ignore', r'.*tempnam.*', RuntimeWarning)

class LockError(exceptions.IOError):
  """Error locking file"""
  def __str__(self):
    args = exceptions.Exception.__str__(self) # Get our arguments
    if(args):      
      return self.__doc__ + ': ' + args
    else:
      return self.__doc__

class NoUnicodeSupportError(LockError):
  """You need at least Python 2.0 compiled with Unicode support"""
class LockFileExistsError(LockError):
  """The .lock-file exists, file locked by someone else"""
class FcntlLockError(LockError):
  """fcntl.lockf call failed - File locked or unsupported"""
class FileChangedError(LockError):
  """File changed during locking"""

class LockFile:
  def __init__(self, file, lockFile=None):
    """File object wrapper for locked files"""
    self._fd = file
    self._lockFile = lockFile
    # Now, this is a bit of magic:
    for dings in dir(self._fd):
      if dings[0] == '_':
        continue
      if dings <> 'close':
        setattr(self, dings, getattr(self._fd, dings))
  def close(self):
    if(self._lockFile):
      try:
        os.unlink(self._lockFile)
      except:
        pass # It's ok, don't worry
    self._fd.close()
  def __del__(self):
    self.close()


def openRead(filename, encoding=None):
  """Opens the file for reading, using shared, non-blocking lock"""
  if(encoding and not codecs):
    raise NoUnicodeSupportError
  count = 0
  while(count < TRIES):
    # Sleeps some if repeated because of failed locking.
    if(count > 0):
      time.sleep(SLEEP_TIME)    
    if(encoding):
      file = codecs.open(filename, 'r', encoding)
    else:
      file = open(filename, 'r')
    # Lock non-blocking shared at first, as we will only read
    try:      
      if(os.path.exists(filename + '.lock')):
        raise LockFileExistsError
      if METHOD == 'fcntl':  
        fcntl.lockf(file.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
      return LockFile(file)
    except IOError, exception:      
      # try one more time.
      count += 1
  else:
    # To many tries, we give up
    raise exception

def openUpdate(filename, create=0, encoding=None):
  """Opens the file for writing (mode +r).
  Uses both exclusive fcntl-locking and dot-locking.
  if create is set, the file is created if it does not
  exist."""
  if(encoding and not codecs):
    raise NoUnicodeSupportError

  filename = os.path.abspath(filename)
  count = 0
  while(count < TRIES):
    # Sleeps some if repeated because of failed locking.
    if(count > 0):
      time.sleep(SLEEP_TIME)

    if(create and not os.path.exists(filename)):
      # Let's create a new file, that we try to make
      tempfile = os.tempnam(os.path.dirname(filename),
                            os.path.basename(filename))
      open(tempfile,'w') # Create (and.. uhu.. possibly overwrite)
      try:
        os.link(tempfile, filename) # Will fail if it exists
      except:
        pass # ignore
      os.unlink(tempfile)

    mode = 'r+' # Open for updating

    if(encoding):
      file = codecs.open(filename, mode, encoding)
    else:
      file = open(filename, mode)

    fileStat = os.stat(filename)      
    # Lock non-blocking exclusive for writing
    try:
      if METHOD=='fcntl':
        fcntl.lockf(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
      elif METHOD=='dotfile':  
        # Create dot-lock-file, with prefix=name of filename
        # Following the dotlocking standard specified in mbox(5)
        tempfile = os.tempnam(os.path.dirname(filename),
                   os.path.basename(filename))
        open(tempfile,'w') # Create (and.. uhu.. possibly overwrite)
        try:
          os.link(tempfile, filename + '.lock') # Will fail if exists
        except OSError:
          raise LockFileExistsError
        if(os.stat(tempfile) <> os.stat(filename + '.lock')):
          raise LockFileExistsError
      os.unlink(tempfile)
      if(os.stat(filename) == fileStat):
        return LockFile(file, filename + '.lock') # End the while loop if we succeed
      else:
        os.unlink(os.stat(filename + '.lock'))
        file.close()
        raise FileChangedError
    except exceptions.Exception, exception: 
      # Try one more time
      count += 1
      if METHOD=='dotlock':
        # Cleanup
        try:
          os.unlink(tempfile)
        except:
          # Would work even if tempfile is not set
          pass
      file.close()

  else:
    # To many tries, we give up
    raise exception
