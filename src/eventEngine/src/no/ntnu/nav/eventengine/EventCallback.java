package no.ntnu.nav.eventengine;

import java.util.*;


public interface EventCallback
{
	public void callback(DeviceDB ddb, int invocationsRemaining);

}
