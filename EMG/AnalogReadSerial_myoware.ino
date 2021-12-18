void setup()
{
    Serial.begin(9600);
    TCCR1A = 0;            // undo the Arduino's timer configuration
    TCCR1B = 0;            // ditto
    TCNT1  = 0;            // reset timer
    OCR1A  = 4;    // period = 4 clock ticks corresponds to 1000Hz sample rate
    TCCR1B = _BV(WGM12)    // CTC mode, TOP = OCR1A
           | _BV(CS12);    // clock at F_CPU/256
    TIMSK1 = _BV(OCIE1A);  // interrupt on output compare A
}

ISR(TIMER1_COMPA_vect)
{
    // OK in test code, don't do this in production code.
    Serial.println(analogRead(A0));
    
}

void loop(){
}
