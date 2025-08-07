set key left top outside noenhanced
set xlabel "T, K"
set ylabel "R, Ohm"
files = system("dir *.dat /b")
#set logscale y
set yrange []
set xrange []
set grid
plot for[f in files] f u 1:3t f w linesp