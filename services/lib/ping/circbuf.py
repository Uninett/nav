"""
A circular buffer. The buffer holds n items. When
the the buffer is full and a new item is added, the
first item is removed.

Original Authors: stain & magnun
"""

class CircBuf:
  def __init__(self, size=10, *args, **kwargs):
      self._size = size
      self._data = [None]*self._size

  def push(self, value):
      self._data.pop()
      self._data.insert(0,value)

  def __len__(self):
      return self._size
  def __getslice__(self, i, j):
      return self._data[i:j]

  def __getitem__(self, i):
      return self._data[i]
          
          
          
    
