#!/bin/sh

cd /home/terom/my_ottd/openttd/

rev=`wget -q -O - http://nightly.openttd.org/devs/rev`
target=r$rev
date=`date +%Y/%m/%d`
time=`date +%H:%M:%S`

if [ -e $target ]; then
    echo Already have $target
else
    echo "Update trunk to r$rev..."
    svn up nightly_trunk -r $rev || exit 1

    echo "Figure out configuration stuff"
    ./openttd.py nightly_trunk || exit 1
    
    echo "Compile..."
    cd nightly_trunk
    make || exit 1
    cd ..
    
    echo "Copy output to rev dir"
    cp -rv nightly_trunk/bin r$rev

    echo "Add to db"
    psql my_ottd myottd_nightly -c "INSERT INTO openttd_versions (name, version) VALUES ('nightly $date', 'r$rev')"

    echo "$date $time: Installed r$rev" >> nightlies.log
fi

