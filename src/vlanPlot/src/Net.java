/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;


class Net extends Canvas implements ItemListener
{
	// Config
	public static final boolean APPLY_LAST_BYNETT = true;
	public static final boolean APPLY_LAST_VLANV = true;

	Com com;
	Color color = Color.black;

	public static final int STRUKTUR_DONE = 0;
	public static final int LAST_DONE = 10;

	public static String netName;
	public static String netLink;

	// Denne styrer om vi har satt konfigurasjon
	public static boolean setConfig = false;

	int x = 10;
	int y = 10;

	int lastx = 0;
	int lasty = 0;

	Nettel visNettel = null;
	//boolean busy;
	int visVlan = 0; // hvilket vlan det fokuseres på
	int visGruppe = -1; // hvilken gruppe det fokuseres på

	//Vector nettel;
	Vector group = new Vector();
	Hashtable nh = new Hashtable();
	Hashtable lh = new Hashtable();
	Hashtable gh = new Hashtable();

	Stack history = new Stack();

	//Polygon bynett;
	//Polygon kjernenett;
	//Polygon testnett;
	Polygon backKnapp;

	// Layout
	LayoutNettel lnTop;
	LayoutNettel lnMiddle;
	LayoutNettel lnBottom;

	boolean needReset = true;
	boolean recordHistory = true;

	// Disse forteller i hvilken modus vi er i
	boolean vlanVandring = false;
	boolean bynettView = false;

	public static int FONT_SIZE = 20;
	//Font overskriftFont = new Font("Helvetica",Font.PLAIN, FONT_SIZE);
	Font overskriftFont = new Font("Arial",Font.BOLD, FONT_SIZE);
	String overskrift = "";

	// Menyer
	PopupMenus vlanMenu;

	// statiske konstanter
	public static final int UPLINK = 0;
	public static final int HZLINK = 1;
	public static final int DNLINK = 2;

	public static final String gwMenuText[] = { "CPU load", "Net-list" };
	public static final String swMenuText[] = { "Backplane load" };
	public static final String linkMenuText[] = { "Load", "Packets", "Drops", "Errors" };
	public static final String linkGwMenuText[] = { "Load", "Packets", "Drops", "Errors", "|"};


	// FIXME: Denne skal være dynamisk!
	//public static final String netNames[] = { "Bynett", "Kjernenett", "Testnett" };

	public Net(Com InCom)
	{
		com = InCom;

		Mouse mouse = new Mouse(com);
		MouseMove mv = new MouseMove(com);
		addMouseListener(mouse);
		addMouseMotionListener(mv);

		Input input = new Input(com);
		com.setInput(input);

		PopupMenuListener pmListener = new PopupMenuListener(com);

		vlanMenu = new PopupMenus("VLAN_MENU", "Vlan meny", this, pmListener);
		PopupMenus gwMenu = new PopupMenus("RUTER_MENU", "Ruter meny", gwMenuText, this, pmListener);
		PopupMenus swMenu = new PopupMenus("SWITCH_MENU", "Svitsj meny", swMenuText, this, pmListener);
		PopupMenus linkMenu = new PopupMenus("LINK_MENU", "Link meny", linkMenuText, this, pmListener);
		PopupMenus linkGwMenu = new PopupMenus("LINK_GW_MENU", "Link Gw meny", linkGwMenuText, this, pmListener);

		com.setGwMenu(gwMenu);
		com.setSwMenu(swMenu);
		com.setLinkMenu(linkMenu);
		com.setLinkGwMenu(linkGwMenu);

		lnTop = new LayoutNettel(this, com.getTopScroll(), "up", com);
		lnMiddle = new LayoutNettel(this, com.getMidScroll(), "hz", com);
		lnBottom = new LayoutNettel(this, com.getBottomScroll(), "dn", com);
		//lnMiddle = new LayoutNettel(this, null, "hz", com);

	}

/*
	public void refetchStrukturInput()
	{
		com.getInput().getDefaultInput();
		com.d("StrukturFetch done.", 1);
		needReset = true;
	}

	public void refetchLastInput()
	{
		//com.getInput().getDefaultLast();
		applyLast();
		com.d("LastFetch done.", 1);
		needReset = true;
	}
*/

/*
	public void fetchDone(int k)
	{
		switch (k)
		{
			case STRUKTUR_DONE:
				buildBynett();
			break;

			case LAST_DONE:
				applyLast();
			break;
		}
	}
*/

	public void buildBynett()
	{
		//String name = (visGruppe < netNames.length) ? netNames[visGruppe] : "nettgruppe "+visGruppe;

		if (visGruppe < 0) visGruppe = 0;
		com.d("Starter buildBynett(), gruppe " + visGruppe, 1);
		com.d("------------", 1);
		com.d("Blanker Nettel-hash", 1);

		// Tar bort scrollbarer
		com.getTopScroll().setVisible(false);
		com.getMidScroll().setVisible(false);
		com.getBottomScroll().setVisible(false);

		// Klargjør for å bygge opp "verden" på nytt
		com.d("Reseter group-vector", 1);
		nh.clear();
		lh.clear();
		group.removeAllElements();
		vlanVandring = false;
		bynettView = true;

		// Hent data
		Hashtable h = com.getInput().getDefaultInput(visGruppe);


		if (!setConfig) {
			Hashtable lConfig = (Hashtable)h.get("listConfig");
			setConfig(lConfig);
		}

		Hashtable lRouters = (Hashtable)h.get("listRouters");
		Hashtable lRouterLinks = (Hashtable)h.get("listRouterLinks");
		Hashtable lRouterLinkInfo = (Hashtable)h.get("listRouterLinkInfo");
		Hashtable lRouterGroups = (Hashtable)h.get("listRouterGroups");
		Hashtable lRouterXY = (Hashtable)h.get("listRouterXY");

		Hashtable lInGroup = new Hashtable();

		com.d("listRouters size: " + lRouters.size(), 2);
		com.d("listRouterLinks size: " + lRouterLinks.size(), 2);
		com.d("listRouteXY size: " + lRouterXY.size(), 2);

		if (visGruppe > 0)
		{
			// Bare ta med enheter som skal være med
			Hashtable tmp = new Hashtable();
			//Hashtable tmp2 = new Hashtable();
			String[] s = (String[])lRouterGroups.get(""+visGruppe);
			for (int i = 4; i < s.length; i++) // Element 2 og 3 er X og Y for gruppen
			{
				// legg til enheten hvis den eksiterer
				if (!lRouters.containsKey(s[i])) continue;
				tmp.put(s[i], lRouters.get(s[i]) );
				lInGroup.put(s[i], lRouters.get(s[i]) );
				com.d("Added: " + s[i],2);
				// sjekk hvilke enheter denne enheten har linker til, og legg til dem
				String[] link = (String[])lRouterLinks.get(s[i]);
				for (int j = 1; j < link.length; j++)
				{
					String[] linkIdS = misc.tokenize(link[j], ",");
					String boksid = linkIdS[1];
					//int linkId = Integer.parseInt(linkIdS[0] );
					//int boksId = Integer.parseInt(linkIdS[1] );

					if (!lRouters.containsKey(boksid)) continue;
					tmp.put(boksid, lRouters.get(boksid) );
				}
			}
			// Så må vi søke gjennom alle stam||elink for å sjekke om noen av dem skal være med
			{
				Enumeration e = lRouterLinks.elements();
				while (e.hasMoreElements())
				{
					String[] link = (String[])e.nextElement();
					if (link[0].charAt(0) == '-')
					{
						// stam||elink
						for (int j = 1; j < link.length; j++)
						{
							String[] linkIdS = misc.tokenize(link[j], ",");
							String boksid = linkIdS[1];

							if (lInGroup.containsKey(boksid) && lRouters.containsKey(link[0]) )
							{
								tmp.put(link[0], lRouters.get(link[0]) );
								break;
							}
						}
					}
				}
			}
			lRouters = tmp;
		}

		/*
		{
			// Debug
			Enumeration e = lRouterXY.elements();
			while (e.hasMoreElements()) {
				String[] s = (String[])e.nextElement();
				com.d("Key: " + s[0] + " X: " + s[1] + " Y: " + s[2], 8);
			}
		}
		*/

		// Legg til rutere
		Enumeration e = lRouters.elements();
		while (e.hasMoreElements()) {
			String[] s = (String[])e.nextElement();

			//com.d("   " + s[0] + ", " + s[1] + "-" + s[3], 3);
			//com.d("   " + s[0] + ", " + s[1] + ", type: " + s[2], 3);

			Nettel n = new Nettel(com, Integer.parseInt(s[0]), s[1], s[2], "1", 0);

			n.setDrawVlan(false);
			n.setHashKey(s[0]);
			nh.put(s[0], n);

			// Sett XY-koordinater
			String[] xy;

			if ( (xy = (String[])lRouterXY.get(s[0])) == null) {
				xy = new String[3];
				xy[1] = "10";
				xy[2] = "25";
			}
			n.setXY(Integer.parseInt(xy[1]), Integer.parseInt(xy[2]) );
			com.d("   " + s[0] + ", " + s[1] + ", type: " + s[2] + " ("+xy[1]+","+xy[2]+")", 3);
			//
		}

		// sett grupper
		e = lRouterGroups.elements();
		com.d("Antall ruter-grupper: " + lRouterGroups.size(), 2);
		while (e.hasMoreElements() && visGruppe == 0)
		{
			String[] s = (String[])e.nextElement();

			if (s.length <= 4 && !s[0].equals("0")) continue; // Det er ingen bokser i denne gruppen

			// Legg til gruppenavnet til GUI-menyen
			com.getLeft().addNettNavn(s[1]);
			if (s[0].equals("0")) continue; // Bynettet

			Grp grp = new Grp(com, Integer.parseInt(s[0]) );
			grp.setName(s[1]);
			grp.setXY(Integer.parseInt(s[2]), Integer.parseInt(s[3]) );
			group.addElement(grp);
			com.d("   Added group (" + s[0] + "): " + s[1] + ", at ("+s[2]+","+s[3]+")", 4);


			for (int j = 4; j < s.length; j++)
			{
				if (!nh.containsKey(s[j])) continue;
				Nettel n = (Nettel)nh.get(s[j]);
				n.setGroupMember(true);
				n.setGroup(Integer.parseInt(s[0]) );
				grp.addMember(n);

				com.d("     grp " + s[0] + ": " + n.getName(), 5);
			}
		}
		com.getLeft().addNettNavn(null); // Listen blir sortert og lukket
		setOverskrift(com.getLeft().getNettNavn(visGruppe)+" for "+netName); // Nå kan vi sette overskrift

		// legg til linker
		e = lRouterLinks.elements();
		com.d("Antall linker     : " + lRouterLinks.size(), 2);
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();

			if (!nh.containsKey(s[0])) {
				com.d("Error: Fant ikke boks med boksid: " + s[0], 3);
				continue;
			}
			Nettel n = (Nettel)nh.get(s[0]);

			com.d("  Legger til linker ut fra("+s[0]+"): " + n.getName() + " ("+(s.length-1)+" stk.)", 5);

			for (int j = 1; j < s.length; j++)
			{
				String[] linkIdS = misc.tokenize(s[j], ",");
				int linkId = Integer.parseInt(linkIdS[0] );
				int boksId = Integer.parseInt(linkIdS[1] );

				String[] linkInfo = (String[])lRouterLinkInfo.get(String.valueOf(linkId));
				Double capacity = Double.valueOf(linkInfo[1] );
				String ifName = (linkInfo.length >= 3) ? linkInfo[2] : "";

				if (!nh.containsKey(""+boksId)) continue;
				Nettel linkTo = (Nettel)nh.get(""+boksId);

				com.d("    Link til ("+boksId+"): " + linkTo.getName() + "(linkId: "+linkId+")", 6);

				// Dersom gruppe, sjekk om denne linken virkelig skal legges til
				if (visGruppe > 0 && !lInGroup.containsKey(""+n.getBoksid()) && !lInGroup.containsKey(""+linkTo.getBoksid()) ) continue;
				//com.d("from: " + n.getFullName() + " to: " + linkTo.getFullName() + " linkFrom: " + lInGroup.containsKey(""+n.getId()) + " linkTo: " + lInGroup.containsKey(""+linkTo.getId()),2);

				Link l;
				if (s[0].charAt(0) != '-')
				{
					// vanlig link
					l = n.addLink( linkTo, linkId, capacity.doubleValue(), -1, ifName );

				} else
				{
					// stam||elink
					l = n.addLink( linkTo, linkId, capacity.doubleValue(), -1, ifName );
					//l.setOspf(linkInfo[8]);
					lh.put("-"+linkId, l);
					l = linkTo.addLink( n, linkId, capacity.doubleValue(), -1, ifName );
				}

				lh.put(""+linkId, l);
				//l.addIpRom(linkInfo[4], linkInfo[5], linkInfo[6], linkInfo[7] );
				//l.setOspf(linkInfo[8]);
			}
		}

		if (APPLY_LAST_BYNETT) {
			applyLast();
		}

		// Så legger vi til tekst for alle bokser
		String[] tList;
		int tcnt=0;
		Hashtable lRouterText = (Hashtable)h.get("listBoksText");
		while ( (tList = (String[])lRouterText.get("t"+tcnt)) != null) {
			String text = tList[1];
			for (int i=2; i < tList.length; i++) {
				String[] data = (String[])lRouterText.get(tList[i]);
				if (data == null) {
					com.d("ERROR in buildBynett(), boksid "+tList[i]+" in t"+tcnt+" is not found in list, check vPServer", 2);
					continue;
				}
				Nettel n = (Nettel)nh.get(tList[i]);
				if (n == null) {
					com.d("ERROR in buildBynett(), could not find boks with id "+tList[i], 2);
					continue;
				}
				n.processText(text, data);
			}
			tcnt++;
		}

		com.d("Behandler listRouterLinkText", 2);
		Hashtable lRouterLinkText = (Hashtable)h.get("listLinkText");
		tcnt=0;
		while ( (tList = (String[])lRouterLinkText.get("t"+tcnt)) != null) {
			String text = tList[1];
			for (int i=2; i < tList.length; i++) {
				String[] data = (String[])lRouterLinkText.get(tList[i]);
				if (data == null) {
					com.d("ERROR in buildBynett(), linkid "+tList[i]+" in t"+tcnt+" is not found in list, check vPServer", 2);
					continue;
				}
				Link l = (Link)lh.get(tList[i]);
				if (l == null) {
					com.d("ERROR in buildBynett(), could not find link with id "+tList[i], 2);
					continue;
				}
				String pText = l.processText(text, data);
				//com.d("  Added text: " + pText, 6);
			}
			tcnt++;
		}


	}

	public void applyLast()
	{
		com.d("Henter last-data", 1);
		com.d("----------------", 1);
		com.getMainPanel().setWaitCursor();

		Hashtable h = com.getInput().getDefaultLast();

		Hashtable gwportOctetLast = (Hashtable)h.get("listGwportOctetLast");
		Hashtable swportOctetLast = (Hashtable)h.get("listSwportOctetLast");
		Hashtable boksCPULast = (Hashtable)h.get("listBoksCPULast");
		Hashtable boksBakplanLast = (Hashtable)h.get("listBoksBakplanLast");

		if (gwportOctetLast == null) gwportOctetLast = new Hashtable();
		if (swportOctetLast == null) swportOctetLast = new Hashtable();
		if (boksCPULast == null) boksCPULast = new Hashtable();
		if (boksBakplanLast == null) boksBakplanLast = new Hashtable();

		com.d("gwportOctetLast size: " + gwportOctetLast.size(), 2);
		com.d("swportOctetLast size: " + swportOctetLast.size(), 2);
		com.d("boksCPULast size: " + boksCPULast.size(), 2);
		com.d("boksBakplanLast size: " + boksBakplanLast.size(), 2);

		// Sett boks-last
		Hashtable[] boksLast = { boksCPULast, boksBakplanLast };
		for (int i=0; i < boksLast.length; i++) {
			Enumeration e = boksLast[i].elements();
			while (e.hasMoreElements()) {
				String[] s = (String[])e.nextElement();
				if (!nh.containsKey(s[0])) continue;
				Nettel n = (Nettel)nh.get(s[0]);
				n.setNettelLast( Double.valueOf(s[1]).doubleValue() );
			}
		}

		// Sett link-last
		Hashtable[] linkLast = { gwportOctetLast, swportOctetLast };
		for (int i=0; i < linkLast.length; i++) {
			Enumeration e = linkLast[i].elements();
			while (e.hasMoreElements()) {
				String[] s = (String[])e.nextElement();
				if (!lh.containsKey(s[0])) continue;

				Link l = (Link)lh.get(s[0]);
				//com.d("  Satt last: " + Double.valueOf(s[1]).doubleValue() , 5);
				l.setLast( Double.valueOf(s[1]).doubleValue() );
				l.recalc();

				if (s.length == 3) {
					// Det er gitt last begge veier her
					if (lh.containsKey("-"+s[0]) ) {
						// Vi forventet også last begge veier, så det er riktig
						l = (Link)lh.get("-"+s[0]);
						l.setLast( Double.valueOf(s[2]).doubleValue() );
						l.recalc();
					} else {
						// Vi forventet ikke last andre veien, men finn likevel linken
						l = l.getLinkOtherWay();
						if (l != null) {
							l.setLast( Double.valueOf(s[2]).doubleValue() );
							l.recalc();
						} else {
							com.d("  Last funnet andre veien, men fant ikke linken tilbake!!", 4);
						}

					}
				}
			}
		}
		com.getMainPanel().setDefaultCursor();
	}


	public void getNettelLinks(Nettel n)
	{
		com.d("Viser sentrisk rundt: " + n.getName() + " Boksid: " + n.getBoksid() + " Type: " + n.getKat() + " Vlan: " + n.getVlan(), 2);

		// Klargjør for å bygge opp "verden" på nytt
		nh.clear();
		lh.clear();
		n.transform();
		bynettView = false;

		// struktur-data
		String[] param;
		{
			Vector v = new Vector();
			if (!setConfig) v.addElement("listConfig");
			if (!com.getLeft().getNetFinalized()) v.addElement("listRouterGroups");

			String[] def = {
				"listBoks"
			};
			param = new String[v.size()+def.length];
			for (int i=0; i < v.size(); i++) param[i] = (String)v.elementAt(i);
			for (int i=0; i < def.length; i++) param[v.size()+i] = def[i];
		}

		String kat = (n.getKat().length() > 0)  ? "&kat="+n.getKat() : "";
		Hashtable h = com.getInput().fetch(param, "boksid="+n.getBoksid()+kat, Input.vPServerURL, String.valueOf(n.getBoksid()) );

		if (!setConfig) {
			Hashtable lConfig = (Hashtable)h.get("listConfig");
			setConfig(lConfig);
		}
		if (!com.getLeft().getNetFinalized()) {
			// Legg til gruppenavnet til GUI-menyen
			Enumeration e = ((Hashtable)h.get("listRouterGroups")).elements();
			while (e.hasMoreElements())
			{
				String[] s = (String[])e.nextElement();
				if (s.length <= 4 && !s[0].equals("0")) continue; // Det er ingen bokser i denne gruppen

				// Legg til gruppenavnet til GUI-menyen
				com.getLeft().addNettNavn(s[1]);
			}
			com.getLeft().addNettNavn(null); // Listen blir sortert og lukket
		}

		Hashtable lNettel = (Hashtable)h.get("listBoks");
		Hashtable lNettelLinks = (Hashtable)h.get("listBoksLinks");
		Hashtable lNettelLinkInfo = (Hashtable)h.get("listBoksLinkInfo");
		Hashtable lLinkVlans = (Hashtable)h.get("listLinkVlans");
		Hashtable lVlanNames = (Hashtable)h.get("listVlanNames");
		Hashtable vlanSet = new Hashtable();

		if (lNettel == null) lNettel = new Hashtable();
		if (lNettelLinks == null) lNettelLinks = new Hashtable();
		if (lNettelLinkInfo == null) lNettelLinkInfo = new Hashtable();
		if (lLinkVlans == null) lLinkVlans = new Hashtable();
		if (lVlanNames == null) lVlanNames = new Hashtable();

		// Fix senter boks
		{
			String[] boksInfo = (String[])lNettel.get(n.getBoksidS());
			if (boksInfo != null) {
				// Lag enhet
				com.d("Oppdaterer senter-nettel: " + n.getName(), 3);
				nh.put(boksInfo[0], n);
				n.setName(boksInfo[1]);
				n.setKat(boksInfo[2]);
			} else {
				com.d("Error, kan ikke oppdaterer senter-nettel, boksid " + n.getBoksidS() + " finnes ikke i svar fra server.", 3);
			}
		}

		// Sjekk om vi skal vise et bestemt vlan eller alle (kun på gw-nivå)
		visVlan = n.getVlan();
		boolean selectVlan = !n.getKat().equalsIgnoreCase("gw");
		if (selectVlan && visVlan == 0) {
			// Vlan ikke spesifisert, da tar vi bare det første over 1 hvis det eksisterer, ellers 1
			Enumeration e = lVlanNames.elements();
			while (e.hasMoreElements()) {
				String[] s = (String[])e.nextElement();
				int v = Integer.parseInt(s[0]);
				com.d("  found vlan: " + v, 1);
				if (v != 1 && (v < visVlan || visVlan == 0)) visVlan = v;
			}
			if (visVlan == 0) {
				//com.d("ERROR! Can't happen, selectVlan && visVlan == 0, n.getName() = " + n.getName() + ", n.getKat() = " + n.getKat(), 2);
				//return;
				com.d("Notice: only vlan 1 found, so using that.", 2);
				visVlan = 1;
			} else {
				com.d("visVlan was 0, using lowest found: " + visVlan, 2);
			}
			n.setVlan(visVlan);
		}
		n.setDrawVlan(false);
		com.d("SelectVlan: " + selectVlan + " Vlan: " + visVlan, 3);

		// sett overskrift
		if (selectVlan) {
			String[] vlanName = (String[])lVlanNames.get(String.valueOf(visVlan));
			if (vlanName != null) {
				setOverskrift("Vlan " + visVlan + " ("+vlanName[1]+") sett fra " + n.getName() );
			} else {
				com.d("Error, vlanName not found for vlan: " + visVlan, 2);
				setOverskrift("Vlan " + visVlan + " (unknown) sett fra " + n.getName() );
			}
			vlanVandring = true;
		} else {
			setOverskrift("Verden sett fra " + n.getName() );
			vlanVandring = false;
		}

		// Gjør klar for å legge til enheter
		lnTop.reset();
		lnBottom.reset();

		// Det er kun en link til hver enhet, vi går derfor over linkene og legger til enhetene fortløpende
		Enumeration e = lNettelLinks.elements();
		while (e.hasMoreElements())
		{
			String[] s = (String[])e.nextElement();
			if (s[0].equals("cn")) continue;

			/*
			// Finn rett linktype
			String linkType = s[0];
			com.d(" Jobber med linktype: " + linkType,5);

			// Finn rett layout-objekt
			LayoutNettel layoutNettel;
			if (linkType.equals("up")) layoutNettel = lnTop; else
			if (linkType.equals("hz")) layoutNettel = lnMiddle; else
			if (linkType.equals("dn")) layoutNettel = lnBottom; else
									   continue;
			layoutNettel.reset();
			//layoutNettel.reset(linkType, antBokser);
			*/

			if (s.length != 3) {
				com.d("Error, s[] has wrong length: " + s.length + ", s[0] = " + s[0],3);
				continue;
			}

			String linkIdUt = s[0];
			String linkIdInn = s[1];
			String boksidTo = s[2];

			// Ser kun på vlan på utgående link
			String[] vlanA = (String[])lLinkVlans.get(linkIdUt);
			if (vlanA == null) {
				com.d("Error, vlan not found for linkIdUt: " + linkIdUt,4);
				continue;
			}

			StringTokenizer st = new StringTokenizer(vlanA[1], ","); // Som default velger vi bare det første vlanet
			String vlan = st.nextToken();
			String retning = st.nextToken();

			int curVlan = (vlan.equals("null")) ? -1 : Integer.parseInt(vlan);
			Vector curVlanList = new Vector();
			if (selectVlan) {
				// Sjekk om enheten virkelig er på dette vlanet
				boolean ok = false;
				for (int j=1; j<vlanA.length; j++) {
					st = new StringTokenizer(vlanA[j], ",");
					vlan = st.nextToken();

					vlanSet.put(vlan, vlan);
					curVlanList.addElement(vlan);
					if (visVlan == Integer.parseInt(vlan)) {
						ok=true;
						retning = st.nextToken();
					}
				}
				if (!ok) continue;
				curVlan = visVlan;
			}

			com.d("  Behandler link til enhet: " + boksidTo,6);

			// Hent info om enhet
			String[] boksInfo = (String[])lNettel.get(boksidTo);
			if (boksInfo == null) continue;

			// Lag enhet
			com.d("   Legger til Nettel, id: " + boksInfo[0] + ", " + boksInfo[1] + ", type: " + boksInfo[2] + " Retning: " + retning + " Vlan: " + curVlan, 5);
			Nettel linkTo = new Nettel(com, Integer.parseInt(boksInfo[0]), boksInfo[1], boksInfo[2], "1", curVlan);
			if (!selectVlan) linkTo.setDrawVlan(true); // Skal tegne vlan-bokser på linkene når det er gw i sentrum

			if (boksInfo.length >= 4 && !boksInfo[3].equals("0")) {
				//com.d("      s[3]: " + boksInfo[3], 6);
				st = new StringTokenizer(boksInfo[3], ",");
				if (st.countTokens() == 2) {
					//com.d("      isclickable: true", 6);
					linkTo.setIsClickable(true);
					linkTo.setClickId(Integer.parseInt(st.nextToken()) );
					linkTo.setClickKat(st.nextToken() );
				}
			}

			// Legg til enheten i nh og i scrollbaren
			nh.put(boksInfo[0], linkTo);
			LayoutNettel layoutNettel = (retning.equals("o")) ? lnTop : lnBottom;
			layoutNettel.addNettel(linkTo);

			String[] linkInfoUt = (String[])lNettelLinkInfo.get(linkIdUt);
			String[] linkInfoInn = (String[])lNettelLinkInfo.get(linkIdInn);
			if (linkInfoUt == null || linkInfoInn == null) continue;
			// FIXME: Skal ikke være nødvendig
			if (linkInfoUt[1].equals("null")) linkInfoUt[1] = (!linkInfoInn[1].equals("null")) ? linkInfoInn[1] : "-1";
			if (linkInfoInn[1].equals("null")) linkInfoInn[1] = linkInfoUt[1];

			// Vi får oppgitt interface navn per link
			String ifNameUt = (linkInfoUt.length >= 3) ? linkInfoUt[2] : "";
			String ifNameInn = (linkInfoInn.length >= 3) ? linkInfoInn[2] : "";

			int last = -1;
			com.d("     Legger til link, utid: " + linkIdUt + ", innid: " + linkIdInn, 8);

			// link ut fra sentrum
			Link linkUt = n.addLink( linkTo, Integer.parseInt(linkIdUt), Double.valueOf(linkInfoUt[1]).doubleValue(), last, ifNameInn );
			// link inn til sentrum
			Link linkInn = linkTo.addLink( n, Integer.parseInt(linkIdInn), Double.valueOf(linkInfoInn[1]).doubleValue(), last, ifNameInn );

			// Hvis linken er blokkert, marker dette
			if (retning.equals("b")) {
				linkUt.setIsBlocked(true);
				linkUt.setDrawBlocked(true);
				linkInn.setIsBlocked(true);
			}

			// Legg til vlan, kun på linken ut
			if (curVlanList.size() > 1) {
				com.d("     curVlanList.size() =  " + curVlanList.size(), 8);
				Com.quickSort(curVlanList);
				for (int i=0; i < curVlanList.size(); i++) {
					String vl = (String)curVlanList.elementAt(i);
					String[] vlanName = (String[])lVlanNames.get(vl);
					if (vlanName == null) continue;
					com.d("       Add vlan: "+vl, 9);
					//linkUt.addVlan(new Integer(vl));
					linkUt.addVlan(vl + " ("+vlanName[1]+")");
				}
			}

			// Legg linkene til linkhash
			lh.put(linkIdUt, linkUt);
			String dash = (linkIdInn.equals(linkIdUt)) ? "-" : "";
			lh.put(dash+linkIdInn, linkInn);

			com.d("     Lagt til link OK", 8);

		} // while

		// Aktiver scrollbarer
		lnTop.activate();
		lnBottom.activate();

		// Oppdatert PopupMeny'en med liste over mulige vlan
		e = vlanSet.elements();
		vlanMenu.clear();
		vlanMenu.setMenuLabel("Skift vlan på "+n.getName());
		com.d("vlanSet size: " + vlanSet.size(), 5);
		while (e.hasMoreElements())
		{
			String vlan = (String)e.nextElement();
			String[] vlanName = (String[])lVlanNames.get(vlan);
			if (vlanName == null) continue;
			Vlan vl = new Vlan(Integer.parseInt(vlan), vlanName[1]);
			com.d("  Added to vlanMenu: " + vlan + " vlanName: " + vlanName[1], 6);
			vlanMenu.addMenuItem(vl);
		}
		vlanMenu.sort();
		vlanMenu.refresh();

		// Hent og legg til last-data
		if (APPLY_LAST_VLANV) {
			applyLast();
		}

		// Så legger vi til tekst for alle bokser
		String[] tList;
		int tcnt=0;
		Hashtable lBoksText = (Hashtable)h.get("listBoksText");
		while ( (tList = (String[])lBoksText.get("t"+tcnt)) != null) {
			String text = tList[1];
			for (int j=2; j < tList.length; j++) {
				String[] data = (String[])lBoksText.get(tList[j]);
				if (data == null) {
					com.d("ERROR in getNettelLinks(), boksid "+tList[j]+" in t"+tcnt+" is not found in list, check vPServer", 2);
					continue;
				}
				Nettel nettel = (Nettel)nh.get(tList[j]);
				if (nettel == null) {
					//com.d("ERROR in getNettelLinks(), could not find boks with id "+tList[j], 2);
					continue;
				}
				nettel.processText(text, data);
			}
			tcnt++;
		}

		com.d("Behandler listRouterLinkText", 2);
		Hashtable lLinkText = (Hashtable)h.get("listLinkText");
		tcnt=0;
		while ( (tList = (String[])lLinkText.get("t"+tcnt)) != null) {
			String text = tList[1];
			for (int j=2; j < tList.length; j++) {
				String[] data = (String[])lLinkText.get(tList[j]);
				if (data == null) {
					com.d("ERROR in getNettelLinks(), linkid "+tList[j]+" in t"+tcnt+" is not found in list, check vPServer", 2);
					continue;
				}
				Link l = (Link)lh.get(tList[j]);
				if (l == null) {
					//com.d("ERROR in getNettelLinks(), could not find link with id "+tList[j], 2);
					continue;
				}
				String pText = l.processText(text, data);
				//com.d("  Added text: " + pText, 6);
			}
			tcnt++;
		}

		com.d("------------------------------------------------------------------------", 1);
	}

	private void setConfig(Hashtable lConfig)
	{
		String[] s = (String[])lConfig.get("vpNetName");
		netName = s[1];

		s = (String[])lConfig.get("vpNetLink");
		netLink = s[1];

		s = (String[])lConfig.get("userName");
		if (s != null) com.d("Found userName: " + s[1], 1);

		s = (String[])lConfig.get("hasAdmin");
		if (s != null) {
			com.d("hasAdmin: " + s[1], 1);
			com.getAdmin().setHasAdmin(new Boolean(s[1]).booleanValue());
		}

		setConfig = true;

	}

	public void recalcLinks()
	{
		// recalc() alle linker
		Enumeration e = nh.elements();
		while (e.hasMoreElements())
		{
			Nettel n = (Nettel)e.nextElement();
			n.recalcLink();
		}
	}

	public void refreshNettel()
	{
		if (!needReset) return;
		needReset = false;

		com.getMainPanel().setWaitCursor();
		if (visNettel == null) showBynett(); else showNettel();
		if (visGruppe == -1) com.getLeft().setNettNavn(""); // Vis blankt menyvalg
		repaint();
		com.getMainPanel().setDefaultCursor();
	}

	private void showBynett()
	{
		//com.getInput().getDefaultInputNotify(visGruppe);

		buildBynett();
		//applyLast();
	}
	private void showNettel()
	{
		visNettel.setSelected(true);
		visNettel.resetLink();
		getNettelLinks(visNettel); // lager en ny nettel Vector med de nye nettel-objektene
		//applyLast();
		//group = new Vector(); // blanker grupper
		group.removeAllElements();
	}

	public void recordHistory()
	{
		if (!recordHistory) return;
		if (visNettel == null)
		{
			// Vi befinner oss i en gruppe, record den
			history.push("-"+visGruppe);
			com.d("Record history: " + "-"+visGruppe,5);
		} else
		{
			// Vis befinner oss på en nettel, record den
			history.push(visNettel.getHashKey());
			com.d("Record history: " + visNettel.getHashKey(),5);
		}
	}
	public void reverseHistory()
	{
		if (history.isEmpty()) return;
		String s = (String)history.pop();
		com.d("Reverse to: " + s,5);
		//String[] h = misc.tokenize(s, ",");
		//int k = Integer.parseInt(h[0]);
		int k = Integer.parseInt(s);
		recordHistory = false;

		if (k <= 0)
		{
			k *= -1;

			// Oppdater GUI-menyen med rett gruppe
			com.getLeft().setNettIndex(k);
			//com.getNet().setVisNettel(null);
			com.getNet().setVisGruppe(k);
			com.d("Refresh nettel...",6);
			com.getNet().refreshNettel();

		} else
		{
			if (!nh.containsKey(s))
			{
				com.d("Error!! Not found in nh, no path back...",5);
				recordHistory = true;
				Enumeration e = nh.keys();
				while (e.hasMoreElements())
				{
					com.d("Key: " + e.nextElement(),6);
				}
				return;
			}
			Nettel n = (Nettel)nh.get(s);
			n.disablePopup();
			if (n.getKat().equals("gw")) n.setVlan(0);
			com.getNet().setVisNettel(n);
			com.d("Refresh nettel...",6);
			com.getNet().refreshNettel();
			//com.getNet().repaint();
		}
		recordHistory = true;
	}




	public void paint(Graphics g)
	{
		final int ANTALL_PASS = 5;

		drawBackKnapp(g);
		drawOverskrift(g);

		/*
		if (busy)
		{
			drawBusy(g);
		}
		*/

		for (int i = 0; i < group.size(); i++) {
			Grp grp = (Grp)group.elementAt(i);
			grp.drawSelf(g);
		}

		for (int i = 1; i <= ANTALL_PASS; i++) {
			Enumeration e = nh.elements();
			while (e.hasMoreElements()) {
				Nettel n = (Nettel)e.nextElement();
				n.drawSelf(g, i);
			}
		}
	}

	public void itemStateChanged(ItemEvent e)
	{
		String nettNavn = ((Choice)e.getSource()).getSelectedItem();
		if (nettNavn.equals(""))
		{
			// Valg det tomme elementet, ikke lov
			if (visGruppe == -1) return;
			com.getLeft().setNettIndex(visGruppe);
		}
		int nett = ((Choice)e.getSource()).getSelectedIndex();

		com.d(" ->Bytter nett til: " + nett, 2);

		//com.getNet().setVisNettel(null);
		com.getNet().setVisGruppe(nett);
		com.getNet().refreshNettel();
	}



	public void drawBackKnapp(Graphics g)
	{
		//int startX = 243;
		//int startY = 1;
		int startX = 15;
		int startY = 3;
		int sizeX = 45;
		int sizeY = 20;

		backKnapp = new Polygon();

		backKnapp.addPoint(startX, startY);
		backKnapp.addPoint(startX+sizeX, startY);
		backKnapp.addPoint(startX+sizeX, startY+sizeY);
		backKnapp.addPoint(startX, startY+sizeY);

		// kant-linjen på knappen
		g.setColor(Color.black);
		g.drawPolygon(backKnapp);
		// bakgrunns-fargen på knappen
		g.setColor(Color.lightGray);
		g.fillPolygon(backKnapp);
		// teksten på knappen
		g.setColor(Color.black);
		g.drawString("Tilbake", startX+3, startY+15);

	}


	public void drawOverskrift(Graphics g)
	{
		//int startX = 310;
		int startX = 70;
		int startY = 5;

		g.setColor(Color.black);

		g.setFont(overskriftFont);
		g.drawString(overskrift, startX+3, startY+15);

	}
	public boolean isBackKnappClicked(int clickX, int clickY) { return backKnapp.contains(clickX, clickY); }

	public void setVisGruppe(int inVisGruppe)
	{
		if (visGruppe != inVisGruppe)
		{
			needReset = true;
			com.getNet().setVisNettel(null);
			recordHistory();
		}
		visGruppe = inVisGruppe;
	}
	public int getVisGruppe() { return visGruppe; }

	//public void setNeedRefetch(boolean b) { needRefetch = b; }
	public void setNeedReset(boolean b) { needReset = b; }

	public void setOverskrift(String s) { overskrift = s; }

	public void settFarge(Color c)
	{
		color = c;
	}

	//public Vector getNettel() { return nettel; }
	public Vector getGrp() { return group; }
	public Hashtable getNettelHash() { return nh; }
	public Hashtable getLinkHash() { return lh; }

	public Nettel getVisNettel() { return visNettel; }
	public void setVisNettel(Nettel InVisNettel)
	{
		if (InVisNettel != null && visNettel == InVisNettel && visVlan != InVisNettel.getVlan()) needReset = true;
		if (visNettel != InVisNettel) needReset = true;
		if (needReset) recordHistory();
		if (needReset && InVisNettel != null)
		{
			visGruppe = -1; // Vi viser nå ingen gruppe
		}
		visNettel = InVisNettel;
	}

	public void changeVisVlan(int vlan)
	{
		if (visNettel == null || visNettel.getVlan() == 0) return; // Kan ikke skifte vlan

		com.d("Changing visVlan: " + vlan, 3);

		visNettel.setVlan(vlan);
		setVisNettel(visNettel);
		refreshNettel();
	}

	public void setVisVlan(int InVisVlan) { visVlan = InVisVlan; }
	public int getVisVlan() { return visVlan; }

	public boolean getVlanVandring() { return vlanVandring; }
	public boolean getBynettView() { return bynettView; }

	public void showVlanPopupMenu(int x, int y)
	{
		vlanMenu.show(this, x, y);
	}



}

class Vlan
{
	int vlan;
	String navn;

	public Vlan(int vlan, String navn)
	{
		this.vlan = vlan;
		this.navn = navn;
	}

	public int getVlan() { return vlan; }

	public String toString()
	{
		return vlan + " ("+navn+")";
	}
}








