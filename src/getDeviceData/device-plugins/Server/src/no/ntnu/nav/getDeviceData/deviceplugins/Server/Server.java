package no.ntnu.nav.getDeviceData.deviceplugins.Server;

import java.util.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxInfo.*;

public class Server implements DeviceHandler
{
    public int canHandleDevice(Netbox nb) {
        if (nb.getCat().equalsIgnoreCase("srv") 
        // snmpMajor is not set yet...
        // && nb.getSnmpMajor() > 0
        ) {
            Log.d("ServerPlugin", "canHandleDevice", "We are ready to serve " + nb.getSysname());
            return DeviceHandler.ALWAYS_HANDLE;
        } 
        Log.d("ServerPlugin", "canHandleDevice", "We cannot serve " + nb.getSysname());
        return DeviceHandler.NEVER_HANDLE;
    }
    public void handleDevice(Netbox nb, SimpleSnmp sSnmp, ConfigParser cp, DataContainers containers) throws TimeoutException {
        Log.setDefaultSubsystem("ServerPlugin");
        NetboxInfoContainer infoContainer = (NetboxInfoContainer)containers.getContainer("NetboxInfoContainer");
        sSnmp.setHost(nb.getIp());
        sSnmp.setCs_ro(nb.getCommunityRo());
        infoContainer.put("blipp", "blapp", "hihi");
        infoContainer.commit();
    }
}
    
