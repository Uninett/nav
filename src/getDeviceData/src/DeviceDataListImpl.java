import java.util.*;
import no.ntnu.nav.getDeviceData.plugins.*;

public class DeviceDataListImpl implements DeviceDataList
{
	DeviceData deviceData;
	List swportDataList = new ArrayList();

	public void setDeviceData(DeviceData deviceData)
	{
		this.deviceData = deviceData;
	}

	public void addSwportData(SwportData swportData)
	{
		swportDataList.add(swportData);
	}

	public DeviceData getDeviceData() { return deviceData; }
	public List getSwportDataList() { return swportDataList; }

}