

. /project/eecs/tinyos/tools/tinyos.sh > /dev/null

EXCLUDE="10.4.2.174\|10.4.3.111\|10.4.3.125\|10.4.3.129\|10.4.3.140\|10.4.3.159\|10.4.3.168\|10.4.3.180\|10.4.3.192\|10.4.3.102\|10.4.3.103\|10.4.3.122\|CO2"

ALIVE=$(mktemp)
MAPPING=$(mktemp)

alive > $ALIVE 2>/dev/null
mapping | grep sdh | sort > $MAPPING
join $ALIVE $MAPPING | grep -ve "$EXCLUDE" | ./mkmniconfig all

rm $ALIVE $MAPPING