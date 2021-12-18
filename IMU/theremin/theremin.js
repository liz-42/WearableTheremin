// Elizabeth Reid, Hedieh Alipour, and Rubia Guerra
// Adapted from reecewgriffith
// https://openprocessing.org/sketch/439399/

var osc, fft;
let serial_pitch;
let serial_vol;
let amplitude;
let pitch;

function setup() {
  // set serial port for pitch control
  serial_pitch = new p5.SerialPort();
  
  var portlist = serial_pitch.list();

  serial_pitch.open("/dev/cu.usbserial-A7006RCv", {baudrate: 115200});
  
  serial_pitch.on('connected', serverConnected);

  serial_pitch.on('list', gotList);

  serial_pitch.on('data', gotData);

  serial_pitch.on('error', gotError);

  serial_pitch.on('open', gotOpen);

  // set serial port for volume control
  serial_vol = new p5.SerialPort();
  
  serial_vol.open("/dev/cu.usbmodem14101", {baudrate: 115200});
  
  serial_vol.on('connected', serverConnected);

  serial_vol.on('list', gotList);

  serial_vol.on('data', gotData_vol);

  serial_vol.on('error', gotError);

  serial_vol.on('open', gotOpen);

  createCanvas(640, 800);

  // set frequency and type
  osc = new p5.TriOsc();
  osc.amp(0.5);

  fft = new p5.FFT();
  osc.start();
}

// There is data available to work with from the serial port
function gotData() {
  var currentString = serial_pitch.readStringUntil("\r\n");

  if (currentString) {
    try {
      pitch = parseFloat(currentString.trim()).toFixed(1);
    }
    catch (TypeError) {
      pitch = 0.0;
    }
    console.log('pitch: ', pitch);
  }
}

// There is data available to work with from the serial port
function gotData_vol() {
  var currentString = serial_vol.readStringUntil("\r\n");

  if (currentString) {
    try {
      amplitude = parseFloat(currentString.trim()).toFixed(1);
    }
    catch (TypeError) {
      amplitude = 0.5;
    }
    console.log('amplitude: ', amplitude);
  }
}

function draw() {
  background(0);

  // analyze the waveform
  var waveform = fft.waveform();
  beginShape();
  stroke(50, 125, 200);
  fill(0);
  strokeWeight(5);
  for (var i = 0; i < waveform.length; i++) {
    var x = map(i, 0, waveform.length, 0, width);
    var y = map(waveform[i], -1, 1, height/2, 0);
    vertex(x, y);
  }
  endShape();

  // change oscillator frequency based on IMU readings
  var freq = map(pitch, -90, 90, 40, 880);
  osc.freq(freq);

  var amp = map(amplitude, -90, 90, 0.01, 1);
  osc.amp(amp);

  line(0, height - 400, width, height - 400);

  textSize(32);
  text("Welcome to the Wearable Theremin", 25, height - 365);
  textSize(22);
  text("by Elizabeth Reid, Hedieh Alipour, and Rubia Guerra", 25, height - 325);
  textSize(12);
  text("Adapted from Reece W. Griffith", 25, height - 285);

  noStroke();
  fill(50, 125, 155);
  textSize(22);
  text("How to use: move both IMUs to interact with the program", 25, height - 225);

  text("Right tilt = +Volume, Left tilt = -Volume", 25, height - 175);
  text("Down = -Pitch, Up = +Pitch", 25, height - 150);
}

// We are connected and ready to go
function serverConnected() {
  print("We are connected!");
}

// Got the list of ports
function gotList(thelist) {
  // theList is an array of their names
  for (var i = 0; i < thelist.length; i++) {
    // Display in the console
    print(i + " " + thelist[i]);
  }
}

// Connected to our serial device
function gotOpen() {
  print("Serial Port is open!");
}

// Ut oh, here is an error, let's log it
function gotError(theerror) {
  print(theerror);
}
