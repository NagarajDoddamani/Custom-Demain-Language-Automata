// Sample program for the custom DSL
num a = 10;
num b = 20;
num c;
dec rate = 2.5;
text message = "Hello DSL";

c = a + b * 2;
show(c);
show(message);

when (c > 30) {
    show(c);
} otherwise {
    show(a);
}

loop (a < 13) {
    a = a + 1;
}

