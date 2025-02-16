# intelino
This Project is a self driving display system for the intelino smart train

the project is in development stage
i am working on the following things:  a webserver where the train track is visualized, and a navigation feature


### You can have undefined amount of trains on an undefined length track

**I recommend as many track switches as posible for efficent colision prevention**


![20250115_180138](https://github.com/user-attachments/assets/7dd8a975-a646-4c84-b9ec-060f019020e6)
*this track is for 2 trains*

---

## How to get started

1. Build a track:
     - the track can't have ends
     - use as many train switches as posible (eg.: 8 for 2 two trains)
     - every switch has to be marked with a uniqe color on the 3. spot (eg.: Cyan,Red,Magenta)  so this switch's name will be Red Magenta, so you can have a Cyan, Blue, Magenta also
     - anywhere where two train tracks cross you have to do this marking (the red can be replaced with any color; and you can have multiple of these with diferent color)
       
       ![Névtelen](https://github.com/user-attachments/assets/f3e1c367-e6e8-40c7-9222-31b1da303190)
     - the track should have no inescapable loops (the trains are not going to go reversed)
       
2. Download the code:
     - copy the repo and install required packages
       ```bash
       git clone https://github.com/b31556/intelino.git
       cd intelino
       pip install -r requirements.txt
     - or manually download and extract it. Then install the packages: `PIL`, `flask`, `intelino.trainlib`, `matplotlib.pyplot`, `networkx`

3. Teach the track:
     - check that all your trains are fully charged up, because they can malfunction if the connection is not fast enough which can happen when not charged fully
     - turn on ONE of you trains put in on the track
     - run the mapper.py  `python mapper.py`
     - the train will map the track and stop when ready  (if your track doesn't meet the requiremts specified above it can couse the train to run infinitly)
     - check the number of switches outputed by the python code if it not matches the actual number of switches try agin from a different location
     - now the traintrack is saved in the map.json
       
4. Start the magic:
     - check that all your trains are fully charged up, because they can malfunction if the connection is not fast enough which can happen when not charged fully
     - turn on all your trains and put them on different locations of the map  (they wont be able to navigate until the first swith where they learn where they are)
     - run the main.py   `python main.py`
     - enter the number of trains
     - wait for them to connect, if it fails try restarting the code and the trains
     - go to your browser and open `localhost:8585`
     - test that everything is working properly
  
       
please consider that the trains can loose connection or the battery can run out which can couse collisions

---

       
       
