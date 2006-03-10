/*
 * NTNU ITEA Nettnu prosjekt
 *
 * Skrvet av: Kristian Eide
 *
 */

import java.util.*;

import java.awt.*;
import java.awt.event.*;


class Admin
{
	Com com;

	// bolske status-variabler
	boolean hasAdmin;
	boolean isAdmin = false;
	boolean moveMode = false;
	String pw;

	public Admin(Com InCom)
	{
		com = InCom;
	}

	public void setHasAdmin(boolean b) { hasAdmin = b; }
	public boolean getHasAdmin() { return hasAdmin; }

	public void setAdmin(boolean InAdmin) { isAdmin = InAdmin; }
	public boolean getAdmin() { return isAdmin; }

	public void setMoveMode(boolean b) { moveMode = b; }
	public boolean getMoveMode() { return moveMode; }

	public void setPw(String s) { pw = s; }
	public String getPw() { return pw; }
}










