/*
 * $Id$
 *
 * Copyright 2002-2004 Norwegian University of Science and Technology
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
 * Author: Kristian Eide <kreide@gmail.com>
 */

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

class Boks
{
	public static boolean DEBUG_OUT = true;
	public static boolean VERBOSE_OUT = true;
	public static final int PROC_UPLINK_LEVEL = Integer.MAX_VALUE;
	Com com;

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

	int numDownlinks;

	public Boks(Com com, int boksid, int gwboksid, List boksbakList, Map bokser, boolean isSW, boolean hasUplink)
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
			String ifindex = s[0];
			int boksbak = Integer.parseInt(s[1]);
			String toIfindex = s[2];

			String mpKey = ifindex;
			BoksMpBak bmp = new BoksMpBak(new Integer(boksbak), toIfindex);

			if (mpKey.equals(uplinkMp)) continue; // Ikke legg til for uplink-porten

			if (boksbak == gwboksid) {
				// Vi har funnet uplink-porten
				uplinkMp = mpKey;
			}

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
			if ( (l=(List)mp.get(mpKey)) == null) {
				if (DEBUG_OUT) outl("---->ifindex: <b>" + ifindex + "</b><br>");
				mp.put(mpKey, l = new ArrayList());
			}

			if (DEBUG_OUT) outl("------>Boksbak("+boksbak+"): <b>" + boksNavn.get(new Integer(boksbak)) + "</b> toIfindex: <b>"+toIfindex+"</b><br>");
			l.add(bmp);

			if (l.size() > maxBehindMp) maxBehindMp = l.size();
		}

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

			if ( (foundUplinkMp() && mpKey.equals(uplinkMp)) && (!isSW || level != PROC_UPLINK_LEVEL && foundUplinkBoksid()) ) continue;

			// Sjekk om vi kan sjekke denne porten på denne level
			if ( ((Integer)mpCount.get(mpKey)).intValue() != level && level != PROC_UPLINK_LEVEL) {
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

				BoksMpBak bmp = (BoksMpBak)l.get(i);
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
			BoksMpBak bmp = (BoksMpBak)entry.getValue();
			boksMp.put(getBoksid()+":"+mpKey, bmp);
		}
	}

	public boolean processLevel(int level) {
		return true;
	}

	public void addUplinkBoksid(BoksMpBak bmp, String myIfindex)
	{
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
			if (DEBUG_OUT) outl("[UPLINK]: Added("+bmp.boksbak+") "+boksNavn.get(bmp.boksbak)+" as a uplink for ("+getBoksid()+") " + getName() + ", ifIndex: " + ifindex + ", isUplink: " + foundUplinkBoksid() + "<br>");
		} else {
			uplinkBoksid = bmp.boksbak;
		}
	}

	public boolean foundUplinkBoksid() { return uplinkBoksid != null; }
	public boolean foundUplinkMp() { return uplinkMp != null; }
	public String getUplinkMp() { return uplinkMp; }

	// Returnerer bak hvilken mp en boksid befinner seg, eller null hvis denne boksen ikke har link til enheten
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
		if (com == null) {
			System.out.println(s);
		} else {
			com.outl(s);
		}
	}

	public String toString() {
		return getName();
	}


}







