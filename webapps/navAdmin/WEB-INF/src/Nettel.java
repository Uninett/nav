/*
 * Nettel.java
 *
 */

import java.io.*;
import java.util.*;

import javax.servlet.*;
import javax.servlet.http.*;

class Boks
{
	static final boolean DEBUG_INPUT = false;

	int nettelid;
	Integer id;
	String[] port;
	int[] idbak;
	int via3;

	String uplinkPort;
	Integer uplink;

	HashMap hm;
	HashMap nettelPort;
	public static HashMap boksNavn;
	public static HashMap boksType;

	ArrayList porter;
	ArrayList downlinks = new ArrayList();

	Com com;

	int numDownlinks;

	public Boks(Com com, String nettelid, String[] port, String[] idbakS, String via3, int begin, int end, HashMap hm)
	{
		this.hm = hm;
		this.com=com;

		this.nettelid=Integer.parseInt(nettelid);
		this.id = new Integer(nettelid);
		this.via3=Integer.parseInt(via3);

		this.port = new String[end-begin];
		this.idbak = new int[end-begin];

		for (int i=0; i < end-begin; i++) {
			this.port[i] = port[begin+i];
			this.idbak[i] = Integer.parseInt(idbakS[begin+i]);
		}
		port=this.port;

		// Finn uplink port
		for (int i=0; i < idbak.length; i++) {
			if (idbak[i] == this.via3) {
				uplinkPort = port[i];
				// Sett uplink direkte mot gw som default
				uplink = new Integer(this.via3);
				break;
			}
		}

		porter = new ArrayList();
		nettelPort = new HashMap();
		if (DEBUG_INPUT) com.outl("-->Nettel: " + nettelid + ", " + nettelNavn.get(new Integer(nettelid)) + " (checking " + port.length + " links)<br>");
		for (int k = 0; k < port.length; )
		{
			if (port[k].equals(uplinkPort)) { k++; continue; }
			if (idbak[k] == this.via3) { k++; continue; }
			if (DEBUG_INPUT) com.outl("---->Port: " + port[k] + "<br>");
			ArrayList l = new ArrayList();

			do {
				if (DEBUG_INPUT) com.outl("------>Adding("+k+"): " + idbak[k] + ", " + nettelNavn.get(new Integer(idbak[k])) + "<br>");
				nettelPort.put(new Integer(idbak[k]), port[k]);
				l.add(new Integer(idbak[k]));
				k++;
			} while (k<port.length && port[k-1].equals(port[k]));

			if (DEBUG_INPUT) com.outl("---->Done("+k+"). total: " + l.size() + "<br>");
			porter.add(l);
		}
		//com.outl("-->Porter size: " + porter.size() + "<br>" );
	}

	public boolean processLevel(int level) {
		boolean done = true;
		boolean addDownl=false;;

		//com.outl("---->Porter size: " + porter.size() + "<br>" );
		for (int i=0; i < porter.size(); i++) {
			ArrayList l = (ArrayList)porter.get(i);
			//com.outl("---->Check size: " + l.size() + "<br>" );
			if (l.size() == level) {
				porter.remove(i); i--;

				String port = (String)nettelPort.get(l.get(0));
				com.out("---->Direct downlink (<b>"+port+"</b>): ");

				boolean b=false;
				int diff=Integer.MAX_VALUE;
				Integer guess=null;
				for (int j=0; j < l.size(); j++) {
					Nettel n = (Nettel)hm.get((Integer)l.get(j));
					int numDownl = (n!=null) ? n.numDownlinks() : -1;

					if (numDownl == level-1 || (level==1 && n==null) ) {
						com.out("(<b>"+nettelNavn.get(l.get(j)) + "</b>,"+numDownl+") ");

						addDownlink((Integer)l.get(j));
						if (n != null) n.setUplink(new Integer(getId()));
						numDownlinks += level;
						addDownl=true;
						b=true;
					} else {
						//com.outl("(No link["+l.get(j)+","+nettelNavn.get(l.get(j))+","+numDownl+"]: " + n + ")");
						if (Math.abs(level-numDownl) < diff) { diff = Math.abs(level-numDownl); guess = (Integer)l.get(j); }
					}

				}
				if (!b) {
					com.out("<b>Warning:</b> No matches for downlink [best guess: ("+guess+")<b>"+nettelNavn.get(guess)+"</b>], candidates are: ");
					for (int j=0; j < l.size(); j++) {
						Nettel n = (Nettel)hm.get((Integer)l.get(j));

						int numDownl = (n!=null) ? n.numDownlinks() : -1;
						com.out("(<b>"+nettelNavn.get(l.get(j)) + "</b>,"+numDownl+") ");
					}
				}
				com.outl("<br>");
			}
		}
		if (addDownl) com.outl("---->Total downlinks: <b>" + numDownlinks + "</b><br>");

		//com.outl("---->After Porter size: " + porter.size() + "<br>" );

		/*
		if (level > 5) return true;

		if (level > 3 && porter.size()>0) {
			ArrayList l = (ArrayList)porter.get(0);
			if (l!=null)
				com.outl("ID: " + nettelid + " size: " + l.size() + " port: " + l.get(0) + "<br>");
		}
		*/

		if (level > 300) return true;

		return porter.size()==0;
	}

	private void addDownlink(Integer nettelid) {
		downlinks.add(nettelid);
	}

	public void setUplink(Integer nettelid) {
		uplink = nettelid;
	}

	public ArrayList getDownlinks() {
		return downlinks;
	}

	public String[][] getFormatedDownlinks() {
		String[][] dl = new String[downlinks.size()][4];

		for (int i=0; i < downlinks.size(); i++) {
			Integer id = (Integer)downlinks.get(i);
			String port = (String)nettelPort.get(id);
			String name = (String)nettelNavn.get(id);
			String type = (String)nettelType.get(id);
			dl[i][0] = ""+id;
			dl[i][1] = port;
			dl[i][2] = name;
			dl[i][3] = type;
		}
		return dl;
	}

	public String[] getUplink() {
		String[] ul = new String[4];
		ul[0] = ""+uplink;
		ul[1] = uplinkPort;
		ul[2] = (String)nettelNavn.get(uplink);
		ul[3] = (String)nettelType.get(uplink);
		return ul;
	}

	public int numDownlinks() {
		return numDownlinks;
	}

	public int getId() {
		return nettelid;
	}

	public Integer getIdInt() {
		return new Integer(getId());
	}

	public String getName() {
		return (String)nettelNavn.get(id);
	}

	public String toString() {
		return getName();
	}


}









