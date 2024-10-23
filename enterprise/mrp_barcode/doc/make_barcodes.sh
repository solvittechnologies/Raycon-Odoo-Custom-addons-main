#!/bin/sh

barcode -t 2x6+20+40 -m 30x30 -p A4 -e code128b -o workorder_barcodes_actions.ps <<BARCODES
O-BTN.button_start
O-BTN.button_pending
O-BTN.record_production
O-BTN.button_scrap
O-BTN.button_finish
O-BTN.button_unblock
BARCODES


# add title in postscript :
#
# /showTitle % stack: str x y
# {
#   /Helvetica findfont 12 scalefont setfont
#   moveto show
# } def
#
# e.g (My Product) 81.65 810 showTitle
