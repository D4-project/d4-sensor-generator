# d4-sensor-generator

d4-sensor-generator is a web interface that aims at helping users configuring
their d4-client, and registering to D4-servers.

The configuration of a client is 6 steps long:

## Welcoming page
![First step](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass1.png)

## Type of client choice

Users choose between the Clang client and the Golang client: [D4 core
client](https://github.com/D4-project/d4-core/tree/master/client) is a simple
and minimal implementation of the [D4 encapsulation
protocol](https://github.com/D4-project/architecture/tree/master/format). There
is also a [portable D4 client](https://github.com/D4-project/d4-goclient) in Go
including the support for the SSL/TLS connectivity for which we provide binaries.

![Client type](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass2.png)

## GOLang client only: Architecture Choice 
Users choose for which architecture they want their client compiled?
![Pre-compiled Binaries](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass3.png)

## Type of data
Users choose which data they intend to send to the D4 server.
![Data type](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass4.png)

## Destination selection
Users choose to which server to want to send their data.
![Destination](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass5.png)

## Registration 
Users can register to the selected server by providing their email address.
![Registration](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass5.png)

## Download final archive
![Download Archive step](https://github.com/D4-project/d4-sensor-generator/blob/master/media/ass5.png)
![Final Archive](https://github.com/D4-project/d4-sensor-generator/blob/master/media/archive.png)
