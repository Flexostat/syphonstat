/*
 * LFreader.c
 *
 * Created: 10/4/2011 4:37:14 PM
 *  Author: soslab
 */ 

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>

#include "pwm.h"
#include "serial.h"
#include "od.h"

#define INTEGRATION_TIME (2*STIR_SPEED/2)  //2 sec

//good to about 1/2 second
void pause(uint16_t duration) {
	uint8_t d = duration/5;
	uint8_t ts = epoch();
	uint8_t t = ts;
	while (((int8_t)(t-ts)) < d) {
		t = epoch();
	}
}


int main(void)
{	
	uint32_t rx_val;
	uint32_t tx_val;
	uint16_t curtime;
	uint16_t close_time;
	DDRB = 0x00;
	DDRD = 0x01<<4; //port D4 output for SPV
	pwm_init();
	usart_init();
	od_init();
	sei();
	od_get_rx();
	od_get_tx();
	uint16_t lastepoch = epoch();
	
    while(1)
    {
		ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
			curtime = epoch();
			if ((curtime-lastepoch) >= INTEGRATION_TIME) {	
				rx_val = od_get_rx();
				tx_val = od_get_tx();
				lastepoch = curtime;
			}
		}		
		
        if (get_rx_len()>0) {
			rawOD r;
			uint8_t cnt = 0;
			uint8_t inchar = read_char();
			r.values[0] = tx_val;
			r.values[1] = rx_val;
			
			while (cnt<sizeof(rawOD)) {
				print_char(r.bytes[cnt]);
				cnt++;
			}
			if (inchar>0) {
				close_time = curtime + ((uint16_t)inchar);
				PORTD |= 0x01<<4; //open SPV
			}
		}
		if ((close_time-curtime)&0x8000) { //if its after close time
			PORTD &= ~(0x01<<4); //close SPV
		}
		
    }
}