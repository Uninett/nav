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
	public static boolean DEBUG_OUT = true;
	public static final int PROC_UPLINK_LEVEL = Integer.MAX_VALUE;
	Com com;

	int boksid;
	Integer boksidI;
	int gwboksid;
	ArrayList boksbakList;
	HashMap mp = new HashMap();
	HashMap mpCount;
	HashMap mpBoksbak = new HashMap();
	HashMap boksbakMp = new HashMap();

	HashMap rawBoksbakMp = new HashMap();

	String uplinkMp;
	Integer uplinkBoksid;

	HashMap bokser;
	boolean isSW;
	boolean hasUplink;

	int maxBehindMp;
	int behindMpCount;

	public static HashMap boksNavn;
	public static HashMap boksType;

	/*
	String uplinkPort;
	Integer uplink;

	HashMap hm;
	HashMap nettelPort;



	ArrayList porter;
	ArrayList downlinks = new ArrayList();
	*/

	int numDownlinks;

	public Boks(Com com, int boksid, int gwboksid, ArrayList boksbakList, HashMap bokser, boolean isSW, boolean hasUplink)
	{
		this.com=com;
		this.boksid = boksid;
		this.gwboksid = gwboksid;
		this.boksbakList = boksbakList;
		boksidI = new Integer(boksid);

		this.bokser = bokser;
		this.isSW = isSW;
		this.hasUplink = hasUplink;
	}

	public void init()
	{
		if (DEBUG_OUT) outl("-->Boks(" + boksid + "): <b>" + boksNavn.get(boksidI) + "</b> (checking " + boksbakList.size() + " links)<br>");

		for (int i=0; i<boksbakList.size(); i++) {
			String[] s = (String[])boksbakList.get(i);
			String modul = s[0];
			String port = s[1];
			int boksbak = Integer.parseInt(s[2]);
			String mpKey = modul+":"+port;

			if (mpKey.equals(uplinkMp)) continue; // Ikke legg til for uplink-porten

			//if (boksbak == gwboksid && hasUplink) {
			if (boksbak == gwboksid) {
				// Vi har funnet uplink-porten
				uplinkMp = mpKey;

				/*
				if (rawBoksbakMp.containsValue(mpKey)) {
					Collection c = rawBoksbakMp.values();
					while (c.remove(mpKey));
				}
				continue;
				*/
			}

			rawBoksbakMp.put(new Integer(boksbak), mpKey);

			ArrayList l;
			if (!mp.containsKey(mpKey)) {
				if (DEBUG_OUT) outl("---->Modul: <b>" + modul + "</b> Port: <b>" + port + "</b><br>");
				mp.put(mpKey, l = new ArrayList());
			} else {
				l = (ArrayList)mp.get(mpKey);
			}

			if (DEBUG_OUT) outl("------>Boksbak("+boksbak+"): <b>" + boksNavn.get(new Integer(boksbak)) + "</b><br>");
			l.add(new Integer(boksbak));

			if (l.size() > maxBehindMp) maxBehindMp = l.size();
		}

		//if (uplinkMp != null) mp.remove(uplinkMp);

		// HashMap som brukes til å hente ut antall enheter bak hver port
		{
			mpCount = new HashMap();
			Iterator iter = mp.entrySet().iterator();
			while (iter.hasNext()) {
				Map.Entry entry = (Map.Entry)iter.next();
				String mpKey = (String)entry.getKey();
				ArrayList l = (ArrayList)entry.getValue();
				mpCount.put(mpKey, new Integer(l.size()));
				behindMpCount += l.size();
			}
		}


		if (DEBUG_OUT) outl("---->Uplink mp is: <b>" + ((uplinkMp!=null)?uplinkMp:"N/A") + "</b><br>" );
		if (DEBUG_OUT) outl("---->Antall porter: <b>" + mp.size() + "</b> behindMpCount: <b>"+behindMpCount+"</b><br>" );

	}

	public boolean proc_mp(int level)
	{
		boolean madeChange = false;
		HashSet removeMp = new HashSet();

		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			ArrayList l = (ArrayList)entry.getValue();

			/*
			if (foundUplinkMp() && mpKey.equals(uplinkMp)) {
				if (!isSW) continue;
				if (level != PROC_UPLINK_LEVEL && foundUplinkBoksid()) continue;
			}
			*/
			if ( (foundUplinkMp() && mpKey.equals(uplinkMp)) && (!isSW || level != PROC_UPLINK_LEVEL && foundUplinkBoksid()) ) continue;


			//if ( ((ArrayList)mpCount.get(mpKey)).size() != level) continue;
			/*
			for (int i=0; i < l.size(); i++) {
				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen

				Integer boksbak = (Integer)l.get(i);
				//outl("Trying to find boksbak: <b>" + boksbak + "</b><br>");
				Boks b = (Boks)bokser.get(boksbak);
				if (b.foundUplinkBoksid()) {
					madeChange = true;

					if (DEBUG_OUT) outl("<font color=red>[Remove]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Removed("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b><br>");

				//if ( ((Boks)bokser.get(l.get(i))).foundUplinkBoksid() ) {
					l.remove(i);
					i--;
				}
			}
			*/

			// Sjekk om vi kan sjekke denne porten på denne level
			if ( ((Integer)mpCount.get(mpKey)).intValue() != level && level != PROC_UPLINK_LEVEL) {
				//int mpCnt = ((Integer)mpCount.get(mpKey)).intValue();
				//if (DEBUG_OUT) outl("<font color=blue>[Level]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> --><b>"+mpCnt+" != " + level + "</b><br>");
				continue;
			}

			if (l.size() == 1) {
				// Funnet en port med kun en enhet, og vi må derfor ha direkte downlink til den
				madeChange = true;
				Integer boksbak = (Integer)l.get(0);
				Boks b = (Boks)bokser.get(boksbak);
				b.addUplinkBoksid(getBoksid());

				// Sett at vi har link til denne enheten
				mpBoksbak.put(mpKey, boksbak);
				boksbakMp.put(boksbak, mpKey);

				if (DEBUG_OUT) outl("<font color=green>[Found]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Boksbak("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b><br>");

				// Vi kan nå ta bort hele listen
				removeMp.add(mpKey);
			}
		}
		if (level == PROC_UPLINK_LEVEL) mp.remove(uplinkMp);
		mp.keySet().removeAll(removeMp);
		return madeChange;
	}

	public void removeFromMp()
	{
		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			ArrayList l = (ArrayList)entry.getValue();

			for (int i=0; i < l.size(); i++) {

				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen
				Integer boksbak = (Integer)l.get(i);
				Boks b = (Boks)bokser.get(boksbak);
				if (b.foundUplinkBoksid() && !b.isSW() ) {
					if (DEBUG_OUT) outl("<font color=red>[Remove]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Removed("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b><br>");
					l.remove(i);
					i--;
				}
			}
		}
	}

	public void guess()
	{
		if (mp.size() == 0) return;

		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			ArrayList l = (ArrayList)entry.getValue();

			// Prøv å gjette hvilken enhet som er riktig, gå ut ifra at SW alltid står over KANT
			int bestGuessIndex = -1;
			for (int i=0; i < l.size(); i++) {
				Boks b = (Boks)bokser.get(l.get(i));
				if (b.isSW()) {
					if (bestGuessIndex == -1) bestGuessIndex = i; else bestGuessIndex = -2;
				}
			}
			if (bestGuessIndex < 0) {
				// Mer enn en SW, gjett på den med høyest antall connections
				int cnt=0;
				for (int i=0; i < l.size(); i++) {
					Boks b = (Boks)bokser.get(l.get(i));
					if (b.getBehindMpCount() > cnt) {
						cnt = b.getBehindMpCount();
						bestGuessIndex = i;
					}
				}
			}

			if (bestGuessIndex >= 0) {
				// Vi har funnet en kandidat, og velger den
				Integer boksbak = (Integer)l.get(bestGuessIndex);
				Boks b = (Boks)bokser.get(boksbak);
				b.addUplinkBoksid(getBoksid());

				// Sett at vi har link til denne enheten
				mpBoksbak.put(mpKey, boksbak);
				boksbakMp.put(boksbak, mpKey);

				if (DEBUG_OUT) outl("<font color=purple>[Guess]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Boksbak("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b><br>");
			}

			/*
			String bestGuess = " Best guess: N/A";
			if (bestGuessIndex >= 0) {
				Boks b = (Boks)bokser.get(l.get(bestGuessIndex));
				bestGuess = " Best guess("+b.getBoksid()+"): <b>"+b.getName()+"</b>";
			}

			com.outl("-->MP: <b>"+mpKey+"</b> Candidates: <b>"+l.size()+"</b>"+bestGuess+"<br>");
			for (int i=0; i < l.size(); i++) {
				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen

				Integer boksbak = (Integer)l.get(i);
				//outl("Trying to find boksbak: <b>" + boksbak + "</b><br>");
				Boks b = (Boks)bokser.get(boksbak);

				com.outl("---->Boksbak("+b.getBoksid()+"): <b>"+b.getName()+"</b><br>");

			}
			*/
		}



	}

	public void report()
	{
		if (mp.size() == 0 && foundUplinkBoksid()) return;

		com.outl("Boks("+getBoksid()+"): <b>"+getName()+"</b> foundUplinkMp: <b>"+foundUplinkMp()+"</b> foundUplinkBoks: <b>"+foundUplinkBoksid()+"</b><br>");

		if (mp.size() == 0) return;

		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			ArrayList l = (ArrayList)entry.getValue();

			if (l.size() == 0) {
				com.outl("-->MP: <b>"+mpKey+"</b> <i>Warning</i>, downlink unit not found!<br>");
				continue;
			}

			// Prøv å gjette hvilken enhet som er riktig, gå ut ifra at SW alltid står over KANT
			int bestGuessIndex = -1;
			for (int i=0; i < l.size(); i++) {
				Boks b = (Boks)bokser.get(l.get(i));
				if (b.isSW()) {
					if (bestGuessIndex == -1) bestGuessIndex = i; else bestGuessIndex = -2;
				}
			}
			if (bestGuessIndex < 0) {
				// Mer enn en SW, gjett på den med høyest antall connections
				int cnt=0;
				for (int i=0; i < l.size(); i++) {
					Boks b = (Boks)bokser.get(l.get(i));
					if (b.getBehindMpCount() > cnt) {
						cnt = b.getBehindMpCount();
						bestGuessIndex = i;
					}
				}
			}

			String bestGuess = " Best guess: N/A";
			if (bestGuessIndex >= 0) {
				Boks b = (Boks)bokser.get(l.get(bestGuessIndex));
				bestGuess = " Best guess("+b.getBoksid()+"): <b>"+b.getName()+"</b>";
			}

			com.outl("-->MP: <b>"+mpKey+"</b> Candidates: <b>"+l.size()+"</b>"+bestGuess+"<br>");
			for (int i=0; i < l.size(); i++) {
				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen

				Integer boksbak = (Integer)l.get(i);
				//outl("Trying to find boksbak: <b>" + boksbak + "</b><br>");
				Boks b = (Boks)bokser.get(boksbak);

				com.outl("---->Boksbak("+b.getBoksid()+"): <b>"+b.getName()+"</b> behindMpCount: <b>"+b.getBehindMpCount()+"</b><br>");

			}
		}

	}

	public void addToMp(HashMap boksMp)
	{
		Iterator iter = mpBoksbak.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			Integer boksbak = (Integer)entry.getValue();
			boksMp.put(getBoksid()+":"+mpKey, boksbak);
		}
	}


	public void oldting()
	{
		/*
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
		if (DEBUG_OUT) com.outl("-->Nettel: " + nettelid + ", " + nettelNavn.get(new Integer(nettelid)) + " (checking " + port.length + " links)<br>");
		for (int k = 0; k < port.length; )
		{
			if (port[k].equals(uplinkPort)) { k++; continue; }
			if (idbak[k] == this.via3) { k++; continue; }
			if (DEBUG_OUT) com.outl("---->Port: " + port[k] + "<br>");
			ArrayList l = new ArrayList();

			do {
				if (DEBUG_OUT) com.outl("------>Adding("+k+"): " + idbak[k] + ", " + nettelNavn.get(new Integer(idbak[k])) + "<br>");
				nettelPort.put(new Integer(idbak[k]), port[k]);
				l.add(new Integer(idbak[k]));
				k++;
			} while (k<port.length && port[k-1].equals(port[k]));

			if (DEBUG_OUT) com.outl("---->Done("+k+"). total: " + l.size() + "<br>");
			porter.add(l);
		}
		//com.outl("-->Porter size: " + porter.size() + "<br>" );
		*/
	}

	public boolean processLevel(int level) {
		/*
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
		*/

		/*
		if (level > 5) return true;

		if (level > 3 && porter.size()>0) {
			ArrayList l = (ArrayList)porter.get(0);
			if (l!=null)
				com.outl("ID: " + nettelid + " size: " + l.size() + " port: " + l.get(0) + "<br>");
		}
		*/

		//if (level > 300) return true;

		//return porter.size()==0;
		return true;
	}

	/*
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
	*/

	public void addUplinkBoksid(int boksid)
	{
		Integer boksbak = new Integer(boksid);
		String mp = null;
		// Først sjekker vi om vi finner enheten på noe annet enn uplink-porten
		if (rawBoksbakMp.containsKey(boksbak)) mp = (String)rawBoksbakMp.get(boksbak);

			//if (foundUplinkMp() && mp.equals(uplinkMp)) {
			//	// Enheten er funnet på uplink-porten
			//	uplinkBoksid = boksbak;
			//}
			//mpBoksbak.put(mp, boksbak);
			//boksbakMp.put(boksbak, mp);
			//com.outl("[BOKS]: Added("+boksid+") "+boksNavn.get(boksbak)+" as a uplink for ("+getBoksid()+") " + getName() + ", MP: " + mp + "<br>");
		//}

		if (mp == null && foundUplinkMp()) mp = uplinkMp;
		if (mp != null) {
			if (mp.equals(uplinkMp)) uplinkBoksid = boksbak;
			mpBoksbak.put(mp, boksbak);
			boksbakMp.put(boksbak, mp);
			if (DEBUG_OUT) com.outl("[UPLINK]: Added("+boksid+") "+boksNavn.get(boksbak)+" as a uplink for ("+getBoksid()+") " + getName() + ", MP: " + mp + ", isUplink: " + foundUplinkBoksid() + "<br>");
		} else {
			uplinkBoksid = boksbak;
		}
	}
	public boolean foundUplinkBoksid() { return uplinkBoksid != null; }
	public boolean foundUplinkMp() { return uplinkMp != null; }
	public String getUplinkMp() { return uplinkMp; }

	// Returnerer bak hvilken mp en boksid befinner seg, eller null hvis denne boksen ikke har link til enheten
	public Mp getMpTo(Integer boksid) { return new Mp((String)boksbakMp.get(boksid)); }

	public int getBehindMpCount() { return behindMpCount; }

	public int getBoksid() {
		return boksid;
	}

	public Integer getBoksidI() {
		return new Integer(getBoksid());
	}

	public String getName() {
		return (String)boksNavn.get(getBoksidI());
	}

	public boolean isSW() { return isSW; }

	// Returnerer det støreste antall enheter bak en port på denne boksen
	public int maxBehindMp() { return maxBehindMp; }


	private void outl(String s) { com.outl(s); }
	private void out(String s) { com.out(s); }

	public String toString() {
		return getName();
	}


}


class Mp
{
	public String modul;
	public String port;
	String mp;

	public Mp(String mp)
	{
		this.mp = mp;
		if (mp != null) {
			StringTokenizer st = new StringTokenizer(mp, ":");
			if (st.countTokens() == 2) {
				modul = st.nextToken();
				port = st.nextToken();
			}
		}
	}

	public String toString()
	{
		return mp;
	}
}






