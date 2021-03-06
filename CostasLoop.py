#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 31 22:25:09 2018

@author: dave
"""
import numpy as np
from scipy.signal import hilbert


class CostasLoop:

  phsVal = []       # Phase modulation vector applied to each input that 
                    # basebands (freq locks) and phase locks to the input
                    # Size n
  output = []       # Basebanded output signal
                    # Size n
  freqInc = []      # Frequency estimate of the pll
                    # Size 1
  bufferSize = []   # Size of input vector to be basebanded
                    # Size 1
  loopFiltFreq = [] # The loop filter frequency coefficient
                    # Size 1
  loopFiltPhs = []  # The loop filter phase coefficient
                    # Size 1


  def __init__(self,loopFiltFreq,loopFiltPhs,bufferSize):
    self.freqInc = 0
    self.bufferSize = bufferSize
    self.loopFiltFreq = loopFiltFreq
    self.loopFiltPhs = loopFiltPhs
    self.output = np.zeros(bufferSize,dtype=np.complex64)
    self.phsVal = np.zeros(bufferSize+1,dtype=np.complex64)


  def run(self,loopInput):

    #import pdb; pdb.set_trace()
    if loopInput.size > self.bufferSize:
      self.bufferSize = loopInput.size
      self.output = np.zeros(self.bufferSize,dtype=np.complex64)
      prevVal = self.phsVal[-1]
      self.phsVal = np.zeros(self.bufferSize+1,dtype=np.complex64)
      self.phsVal[-1] = prevVal
    
    # Execute the costas loop
    # Normalize the input.  Allows the loop filter gain to not depend on the
    # input signal amplitude
    loopInput = loopInput / np.max(np.abs(loopInput))
    
    # Is the input is not complex (analytic), create a complex (analytic) 
    # representation
    if not(np.iscomplexobj(loopInput)):
      loopInput = hilbert(loopInput)
    
    # Loop over the input
    for ndx in range(len(loopInput)):

      # Create the basebanded signal
      if ndx == 0:
        # This is the first iteration in this block.  Act as a circular buffer 
        # and wrap to the last value of the previous iteration through the 
        # buffer to maintain coherency
        self.phsVal[0] = self.phsVal[-1]
      
      # Modulate the input by the VCO and store in an output array
      self.output[ndx] = loopInput[ndx] * np.exp(1j*self.phsVal[ndx])
      
      # Calculate the individual I and Q values, to be used to compute the 
      # error signal
      realVal = np.real(self.output[ndx])
      imagVal = np.imag(self.output[ndx])
      
      # Calculate the latest error signal.  Note, I don't believe I need to 
      # worry about filtering the I/Q to remove the 2Wc component because the 
      # NCO is being  applied as an analytic signal
      errSig = realVal * imagVal
      # Apply the loop filter and calculate the most recent error to be fed 
      # into the NCO.  Track frequency and phase necessary to lock.
      self.freqInc += self.loopFiltFreq * errSig
      phsInc = self.loopFiltPhs * errSig + self.freqInc
      
      # Update the phase of the next NCO output sample
      self.phsVal[ndx+1] = self.phsVal[ndx] + phsInc
      
    self.output = self.output * np.exp(1j*np.pi/2);