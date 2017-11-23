#! /bin/bash
# rsync -rvz --exclude '.git' -e "ssh -p 22" ../lib_p_bz bigzhu@follow.center:/home/bigzhu/
# rsync -rvz --exclude '.git' -e "ssh -p 22" ./* bigzhu@follow.center:/home/bigzhu/follow_center_p/

rsync -rvz --exclude '.git' -e "ssh -p 2222" ../lib_py root@47.88.137.77:/home/bigzhu/
rsync -rvz --exclude '.git' -e "ssh -p 2222" ./* root@47.88.137.77:/home/bigzhu/follow_center_p2/
