# end2end_delay
This application is a simple python application intended to measure end-to-end delay.
It assembles a pure ethernet packet with a payload of the timestamp of the sending, and after 
receiving the packet on the other side, this app calculates the difference.
Clearly, it could only work well if the sending and receiving side is on the same machine, thus
it is possible to avoid issues about clock synchronizations among multiple machines.

So, this app is useful for testing a simple network function's (or a given service chain) 
delay to which this application is connected via two interfaces.

## Why and when to use?
If the path from the measuring machine to the network function (or service chain) 
and the path from the network function (or service chain) to the measuring machine is the same, 
then the results are not going to be different than dividing the RTT with 2.
However,even if this is the case, this application ease your way to getting that information, since
no higher level settings (such as IP addresses) are needed, end the used interfaces do not need
to be separated in different networking namespaces.

#
   +--------+    +---------+
   |end2end |----| Network |
   |delay   |    | func. or|
   |meas.   |----| ser.cha.|
   +--------+    +---------+



On the other hand, if the above-mentioned paths are not equal, then RTT/2 may not result in the
exact delay.

   +--------+    +---------+      +---+       +-----+
   |end2end |----| Network |------|   |       | VNF |
   |delay   |    | func.   |      |   | . . . |     |---+
   |meas.   |    |         |      |   |       +-----+   |
   +--------+    +---------+      +---+                 |
       |                                                |
       |                                                |
       +------------------------------------------------+


#Note
In a real-time OS, this application probably works more precise

#USAGE:
$ sudo start.sh <iface_sender> <iface_reciever>

Do not run end2end_delay.py manually, start.sh does the job for you.
It will bring up the interfaces in promiscuous mode, and the measurement then will be started
in two xterms!
If you have no GUI/display manager, then modify start.sh accordingly, or set up your interfaces
manually, first start the reciever side:
$ sudo python end2end_delay server <iface>
Then, on another terminal, start the sender side:
$ sudo python end2end_delay client <iface2>



