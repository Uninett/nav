package no.ntnu.nav.eventengine;

import java.util.*;


public interface EventHandler
{

	public String[] handleEventTypes();
	public void handle(DeviceDB ddb, Event e);

}
