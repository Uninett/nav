TOPSRCDIR=$(cd ../..; printf %s "$PWD")
MKFILEDIR=$PWD
USERID=$(id -u)
GROUPID=$(id -g)
DOCKERFILE=Dockerfile

NAME=navtest:$(git describe --tags)-$DOCKERFILE


case $1 in

    build)
        docker build -t $NAME -f $DOCKERFILE $MKFILEDIR
        ;;
    buildnocache)
        docker build --no-cache -t $NAME -f $DOCKERFILE $MKFILEDIR
        ;;
    check)
        docker run -t -u $USERID:$GROUPID -v /$TOPSRCDIR:/source --tmpfs //var/lib/postgresql $NAME //source/tests/docker/test.sh
        ;;
    shell)
        docker run -ti --rm -u $USERID:$GROUPID -v /$TOPSRCDIR:/source --tmpfs //var/lib/postgresql $NAME //bin/bash
        ;;

esac
