/*
 * $Id:$
 *
 * Copyright 2004 Norwegian University of Science and Technology
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Kristian Eide <kreide@online.no>
 */

import java.io.*;
import java.util.*;

class Boks
{
	public static boolean DEBUG_OUT = true;
	public static boolean VERBOSE_OUT = true;
	public static final int PROC_UPLINK_LEVEL = Integer.MAX_VALUE;

	int boksid;
	Integer boksidI;
	int gwboksid;
	List boksbakList;
	Map mp = new HashMap();
	Map mpCount;
	Map mpBoksbak = new HashMap();
	Map boksbakMp = new HashMap();

	Map rawBoksbakMp = new HashMap();

	String uplinkMp;
	Integer uplinkBoksid;

	Map bokser;
	boolean isSW;
	boolean hasUplink;

	int maxBehindMp;
	int behindMpCount;

	public static Map boksNavn;
	public static Map boksType;

	/*
	String uplinkPort;
	Integer uplink;

	HashMap hm;
	HashMap nettelPort;



	ArrayList porter;
	ArrayList downlinks = new ArrayList();
	*/

	int numDownlinks;

	public Boks(int boksid, int gwboksid, List boksbakList, Map bokser, boolean isSW, boolean hasUplink)
	{
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
			String ifindex = s[0];
			int boksbak = Integer.parseInt(s[1]);
			String toIfindex = s[2];

			//String mpKey = modul+":"+port;
			String mpKey = ifindex;
			BoksMpBak bmp = new BoksMpBak(new Integer(boksbak), toIfindex);

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

			//rawBoksbakMp.put(new Integer(boksbak), mpKey);
			if (toIfindex == null) {
				if (rawBoksbakMp.containsKey(new Integer(boksbak))) {
					// Oh oh, nå er vi i trøbbel, da det er flere linker til denne enheten uten at vi vet mp bak
					// (og da går vi ut ifra at andre siden heller ikke vet vår mp)
					outl("---->[<font color=red>WARNING</font>]: Boks(" + boksid + "): <b>" + boksNavn.get(boksidI) + "</b>, mer enn en link til boks("+boksbak+") "+boksNavn.get(new Integer(boksbak))+", uten at vi vet mp i andre enden.<br>");
				} else {
					rawBoksbakMp.put(new Integer(boksbak), mpKey);
				}
			}

			List l;
			/*
			if (!mp.containsKey(mpKey)) {
				if (DEBUG_OUT) outl("---->Modul: <b>" + modul + "</b> Port: <b>" + port + "</b><br>");
				mp.put(mpKey, l = new ArrayList());
			} else {
				l = (ArrayList)mp.get(mpKey);
			}
			*/
			if ( (l=(List)mp.get(mpKey)) == null) {
				if (DEBUG_OUT) outl("---->ifindex: <b>" + ifindex + "</b><br>");
				mp.put(mpKey, l = new ArrayList());
			}

			if (DEBUG_OUT) outl("------>Boksbak("+boksbak+"): <b>" + boksNavn.get(new Integer(boksbak)) + "</b> toIfindex: <b>"+toIfindex+"</b><br>");
			l.add(bmp);

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
				List l = (List)entry.getValue();
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
		Set removeMp = new HashSet();

		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			List l = (List)entry.getValue();

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

				// Porten på denne siden
				BoksMpBak myBmp = new BoksMpBak(getBoksid(), mpKey);
				BoksMpBak bmp = (BoksMpBak)l.get(0);

				// Hent boksen fra mpBoksbak hvis den finnes der
				if (mpBoksbak.containsKey(mpKey)) {
					BoksMpBak bmpA = (BoksMpBak)mpBoksbak.get(mpKey);
					if (!bmp.boksbak.equals(bmpA.boksbak)) {
						outl("<font color=red>[WARNING]</font> Conflicting boksbak in mp vs. mpBoksbak for Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> bmp: " + bmp + ", bmpA: " + bmpA + " <br>");
					}
					bmp = bmpA;
				}

				Boks b = (Boks)bokser.get(bmp.boksbak);
				if (bmp.toIfindex == null && b.foundUplinkMp()) {
					// Vi velger bare uplink-porten siden vi er direkte uplink
					bmp.setToIfindex(b.getUplinkMp());
				}

				b.addUplinkBoksid(myBmp, bmp.toIfindex);

				// Sett at vi har link til denne enheten
				mpBoksbak.put(mpKey, bmp);
				boksbakMp.put(bmp.hashKey(), mpKey);

				if (DEBUG_OUT) outl("<font color=green>[Found]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Boksbak("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b> bmp: " + bmp + "<br>");

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
			List l = (List)entry.getValue();

			for (int i=0; i < l.size(); i++) {

				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen
				BoksMpBak bmp = (BoksMpBak)l.get(i);
				//Integer boksbak = (Integer)l.get(i);
				Boks b = (Boks)bokser.get(bmp.boksbak);
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
			List l = (List)entry.getValue();

			// Prøv å gjette hvilken enhet som er riktig, gå ut ifra at SW alltid står over KANT
			int bestGuessIndex = -1;
			for (int i=0; i < l.size(); i++) {
				Boks b = (Boks)bokser.get( ((BoksMpBak)l.get(i)).boksbak );
				if (b.isSW()) {
					if (bestGuessIndex == -1) bestGuessIndex = i; else bestGuessIndex = -2;
				}
			}
			if (bestGuessIndex < 0) {
				// Mer enn en SW, gjett på den med høyest antall connections
				int cnt=0;
				for (int i=0; i < l.size(); i++) {
					Boks b = (Boks)bokser.get( ((BoksMpBak)l.get(i)).boksbak );
					if (b.getBehindMpCount() > cnt) {
						cnt = b.getBehindMpCount();
						bestGuessIndex = i;
					}
				}
			}

			if (bestGuessIndex >= 0) {
				// Porten på denne siden
				BoksMpBak myBmp = new BoksMpBak(getBoksid(), mpKey);

				// Vi har funnet en kandidat, og velger den
				BoksMpBak bmp = (BoksMpBak)l.get(bestGuessIndex);
				Boks b = (Boks)bokser.get(bmp.boksbak);

				if (bmp.toIfindex == null && b.foundUplinkMp()) {
					// Vi velger bare uplink-porten siden vi er direkte uplink
					bmp.setToIfindex(b.getUplinkMp());
				}

				b.addUplinkBoksid(myBmp, bmp.toIfindex);

				// Sett at vi har link til denne enheten
				mpBoksbak.put(mpKey, bmp);
				boksbakMp.put(bmp.hashKey(), mpKey);

				if (VERBOSE_OUT) outl("<font color=purple>[Guess]</font> Boks("+getBoksid()+"): <b>" + getName() + "</b> Mp: <b>"+mpKey+"</b> Boksbak("+b.getBoksid()+"</b>): <b>" + b.getName() + "</b><br>");
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

		outl("Boks("+getBoksid()+"): <b>"+getName()+"</b> foundUplinkMp: <b>"+foundUplinkMp()+"</b> foundUplinkBoks: <b>"+foundUplinkBoksid()+"</b><br>");

		if (mp.size() == 0) return;

		Iterator iter = mp.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			List l = (List)entry.getValue();
			
			if (l.size() == 0) {
				outl("-->MP: <b>"+mpKey+"</b> <i>Warning</i>, downlink unit not found!<br>");
				continue;
			}

			// Prøv å gjette hvilken enhet som er riktig, gå ut ifra at SW alltid står over KANT
			int bestGuessIndex = -1;
			for (int i=0; i < l.size(); i++) {
				Boks b = (Boks)bokser.get( ((BoksMpBak)l.get(i)).boksbak );
				if (b.isSW()) {
					if (bestGuessIndex == -1) bestGuessIndex = i; else bestGuessIndex = -2;
				}
			}
			if (bestGuessIndex < 0) {
				// Mer enn en SW, gjett på den med høyest antall connections
				int cnt=0;
				for (int i=0; i < l.size(); i++) {
					Boks b = (Boks)bokser.get( ((BoksMpBak)l.get(i)).boksbak );
					if (b.getBehindMpCount() > cnt) {
						cnt = b.getBehindMpCount();
						bestGuessIndex = i;
					}
				}
			}

			String bestGuess = " Best guess: N/A";
			if (bestGuessIndex >= 0) {
				Boks b = (Boks)bokser.get( ((BoksMpBak)l.get(bestGuessIndex)).boksbak );
				bestGuess = " Best guess("+b.getBoksid()+"): <b>"+b.getName()+"</b>";
			}

			outl("-->MP: <b>"+mpKey+"</b> Candidates: <b>"+l.size()+"</b>"+bestGuess+"<br>");
			for (int i=0; i < l.size(); i++) {
				// Sjekk om vi allerede har funnet uplink for denne enheten, i så tilfellet tar vi den ut fra listen

				//Integer boksbak = (Integer)l.get(i);
				BoksMpBak bmp = (BoksMpBak)l.get(i);
				//outl("Trying to find boksbak: <b>" + boksbak + "</b><br>");
				Boks b = (Boks)bokser.get(bmp.boksbak);

				outl("---->Boksbak("+b.getBoksid()+"): <b>"+b.getName()+"</b> behindMpCount: <b>"+b.getBehindMpCount()+"</b><br>");

			}
		}

	}

	public void addToMp(Map boksMp)
	{
		Iterator iter = mpBoksbak.entrySet().iterator();
		while (iter.hasNext()) {
			Map.Entry entry = (Map.Entry)iter.next();
			String mpKey = (String)entry.getKey();
			//Integer boksbak = (Integer)entry.getValue();
			BoksMpBak bmp = (BoksMpBak)entry.getValue();
			boksMp.put(getBoksid()+":"+mpKey, bmp);
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

	public void addUplinkBoksid(BoksMpBak bmp, String myIfindex)
	{
		/*
		if (getBoksid() == 716 && bmp.boksbak.equals(new Integer(708))) {
			System.err.println("boksbak: "+bmp.boksbak+" modulbak: " + bmp.modulbak + " portbak: " + bmp.portbak);
		}
		*/
		String ifindex = null;
		if (myIfindex != null) {
			ifindex = myIfindex.toString();
		} else {
			ifindex = (String)rawBoksbakMp.get(bmp.boksbak);
		}

		if (ifindex == null && foundUplinkMp()) ifindex = uplinkMp;
		if (ifindex != null) {
			if (ifindex.equals(uplinkMp)) uplinkBoksid = bmp.boksbak;
			mpBoksbak.put(ifindex, bmp);
			boksbakMp.put(bmp.hashKey(), ifindex);
			if (DEBUG_OUT) outl("[UPLINK]: Added("+bmp.boksbak+") "+boksNavn.get(bmp.boksbak)+" as an uplink for ("+getBoksid()+") " + getName() + ", ifIndex: " + ifindex + ", isUplink: " + foundUplinkBoksid() + "<br>");
		} else {
			uplinkBoksid = bmp.boksbak;
		}
	}

	/*
	public void addUplinkBoksid2(int boksid)
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
			if (DEBUG_OUT) outl("[UPLINK]: Added("+boksid+") "+boksNavn.get(boksbak)+" as a uplink for ("+getBoksid()+") " + getName() + ", MP: " + mp + ", isUplink: " + foundUplinkBoksid() + "<br>");
		} else {
			uplinkBoksid = boksbak;
		}
	}
	*/
	public boolean foundUplinkBoksid() { return uplinkBoksid != null; }
	public boolean foundUplinkMp() { return uplinkMp != null; }
	public String getUplinkMp() { return uplinkMp; }

	// Returnerer bak hvilken mp en boksid befinner seg, eller null hvis denne boksen ikke har link til enheten
	//public Mp getMpTo(Integer boksid) { return new Mp((String)boksbakMp.get(boksid)); }
	//public Mp getMpTo(int boksid, String modulbak, String portbak) { return new Mp((String)boksbakMp.get(boksid+":"+modulbak+":"+portbak)); }
	public String getIfindexTo(int boksid, String toIfindex) { return (String)boksbakMp.get(boksid+":"+toIfindex); }

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


	private void outl(String s)
	{
		System.out.println(s);
	}
	private void out(String s)
	{
		System.out.print(s);
	}
	/*
	private void outl(String s) { System.err.println("outl: " + s + " com: " + com); com.outl(s); }
	private void out(String s) { com.out(s); }
	*/

	public String toString() {
		return getName();
	}


}







