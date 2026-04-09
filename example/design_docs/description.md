# Background and Goal

## background

What triggered us to make this project is the project made by a freshman when his CS course. He made a small game called *四国战争*. A turn based RTS game played by four. There are some units like infantry tank, fighter, and ... even nuke boom. This made me think of that try I've made at the tail of High school. I was trying to develop an event system that could support a simplified version of Star Rail by Python. I found that system can be implied almost directly on this new project. And in further consideration, I found it may be a very universal solution. I do think this idea may have been implemented by others. However, I still want to make this by myself. Besides, this may have been refined into a face that I can't figure out its original shape in real engineering project. 

# Goal

I think that goal of this project have shown its tail: We want to implement an event system that could support most of turn-based, or to say that, event based, synchronized game. If we can be more arrogant, we want to develop and game engine.

# Idea and Technique description

This system is event-based. This determines event as the most important and basic class. And the main function is to maintain a priority queue that contains many events with different priorities. BTW, on account of efficiency, we may consider priority queue that support multiprocessing (though this may cause some chaos of order, but this could be discussed later). Beyond the event queue, we should have a listening pool that contains many state or trigger, or other things that can conditionally produce new events. And an or some handler while request event from queue and process event triggered which will be added into queue.

Because by lack on knowledge, maybe some details have more mature solution, which you can inform me and let us discuss.

One thing very important is clear: how to design the event class. This should only be settled after long and complementary research. This depends on and determine the capacity of our engine. As the ultimate goal, we certainly hope it can be qualified to as much work as it can be. Though, this may go too ideal to be real. Anyway, we can try our best in first run, and check if it can be further enhancement after demo can run. 