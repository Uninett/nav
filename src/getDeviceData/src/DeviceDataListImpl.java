import java.util.*;
import no.ntnu.nav.getDeviceData.plugins.*;

public class DeviceDataListImpl implements DeviceDataList
{
	DeviceData deviceData;
	List moduleDataList = new ArrayList();

	public void setDeviceData(DeviceData deviceData)
	{
		this.deviceData = deviceData;
	}

	public void addModuleData(ModuleData moduleData)
	{
		moduleDataList.add(moduleData);
	}

	public DeviceData getDeviceData() { return deviceData; }
	public List getModuleDataList() { return moduleDataList; }

}