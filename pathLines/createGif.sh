#!/bin/bash
convert $(for a in $1/**.png; do printf -- "-delay 10 %s " $a; done; ) animation.gif
