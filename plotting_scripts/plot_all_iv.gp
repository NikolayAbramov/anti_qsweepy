set key left top outside noenhanced
set xlabel "I, A"
set ylabel "V, Volt"
files = system("dir *.dat /b")
#set logscale y
set yrange []
set xrange []
set grid
plot for[f in files] f u 1:2 t f w linesp