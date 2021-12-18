/**
 * Elizabeth Reid, Hedieh Alipour, and Rubia Guerra
 * Adapted from:
 * Processing Sound Library, Example 2
 *
 */


import processing.sound.*;
import processing.serial.*;

TriOsc triOsc;

float amplitude = 0.5;

Serial myPort_freq;  // Create object from Serial class
Serial myPort_vol;  // Create object from Serial class

int[] stepSequence = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24 };
String[] notes = { "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4", "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5", "C6" };

// An index to count up the notes
int note = 0;

void setup() {
  size(640, 360);
  background(255);

  // Create triangle wave and start it
  triOsc = new TriOsc(this);

  // serial port stuff
  String portName_freq = "/dev/cu.usbserial-A7006RCv";
  String portName_vol = "/dev/cu.usbmodem14201";
  myPort_freq = new Serial(this, portName_freq, 115200);
  myPort_vol = new Serial(this, portName_vol, 115200);

  triOsc.play();
}

void draw() {
  background(255);
  if ( myPort_freq.available() > 0)
  {  // If data is available,
    String str = myPort_freq.readStringUntil('\n');
    if (str != null) {
      try
      {
        float temp = Float.parseFloat(str.trim());
        int note = int(temp);
        println(note);
        if ( myPort_vol.available() > 0)
        {  // If data is available,
          String str_vol = myPort_vol.readStringUntil('\n');
          if (str_vol != null) {
            try
            {
              float temp_vol = Float.parseFloat(str_vol.trim());
              float amplitude = temp_vol / 24.0;
              println(amplitude);
              // If the determined trigger moment in time matches up with the computer clock and
              // the sequence of notes hasn't been finished yet, the next note gets played.
              // analyze the waveform
              beginShape();
              stroke(0, 255, 50);
              fill(0);
              strokeWeight(5);
              text("Note: " + notes[note + 1], width /4, height / 2);
              text("Frequency (Hz): " + nf(stepToFreq(stepSequence[note]), 0, 2), width /2, height / 2);
              text("Amplitude (0-1): " + nf(amplitude, 0, 2), width / 2, height / 3);


              triOsc.play(stepToFreq(note), amplitude);
            }
            catch(NumberFormatException ex)
            {
              println("invalid input");
            }
          }
        }
      }
      catch(NumberFormatException ex)
      {
        println("invalid input");
      }
    }
  }
}

// This helper function calculates the respective frequency of a note step
float stepToFreq(int note) {
  return (pow(2, ((note)/12.0))) *  261.63;
}
