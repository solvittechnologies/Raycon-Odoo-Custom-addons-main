#!/bin/sh

barcode -t 2x7+40+40 -m 50x30 -p A4 -e code128b -o barcodes_demo_data.ps <<BARCODES
054398267125
204539674215
420196872340
601647855631
LOC-01-00-00
LOC-01-01-00
LOC-01-01-01
LOC-01-02-00
LOC-02-00-00
PACK0000001
WH/OUT/00005
WH/IN/00003
LOT-000001
LOT-000002
BARCODES

barcode -t 2x7+40+40 -m 50x30 -p A4 -e code128b -o barcodes_actions.ps <<BARCODES
O-CMD.MAIN-MENU
O-CMD.CANCEL
O-CMD.EDIT
O-CMD.SAVE
O-BTN.validate
O-BTN.print
O-BTN.put-in-pack
O-BTN.button_scrap
O-CMD.PAGER-PREV
O-CMD.PAGER-NEXT
O-CMD.PAGER-FIRST
O-CMD.PAGER-LAST
BARCODES

# add title in postscript :
#
# /showTitle % stack: str x y
# {
#   /Helvetica findfont 12 scalefont setfont
#   moveto show
# } def
#
# (iPad Mini) 81.65 810 showTitle
