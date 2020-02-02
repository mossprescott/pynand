set -e

DIR=$(dirname $0)

$DIR/../../nand2tetris/tools/JackCompiler.sh $DIR/nand-mines/src

mv $DIR/nand-mines/src/*.vm $DIR