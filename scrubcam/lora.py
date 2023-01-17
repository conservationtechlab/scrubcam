"""Tools for using with LoRa packet radio hardware

On some ScrubCam devices LoRa packet radio hardware is equipped to
send reports back to hubs.  Code for interfacing with those is
included here.

"""


import busio
from digitalio import DigitalInOut
import board
import adafruit_rfm9x


class LoRaSender():
    """Manages sending messages on LoRa radio

    Specifically interfaces with the RFM9x module that we are
    currently connecting to the ScrubCam as part of the Adafruit
    Radio+OLED Bonnet.

    """

    def __init__(self):
        cs = DigitalInOut(board.CE1)  # pylint: disable=invalid-name
        reset = DigitalInOut(board.D25)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)
        self.rfm9x.tx_power = 23

    def send(self, data_strg):
        """"Send a string on LoRa Radio

        Parameters
        ----------

        data_strg : string
            Data to send over LoRa

        """
        send_data = bytes(f'{data_strg}\r\n', 'utf-8')
        self.rfm9x.send(send_data)
