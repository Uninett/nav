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


public class BoksMpBak
{
	public Integer boksbak;
	public String toIfindex;

	String hashKey;

	public BoksMpBak(int boksbak, String toIfindex)
	{
		this(new Integer(boksbak), toIfindex);
	}

	public BoksMpBak(Integer boksbak, String toIfindex)
	{
		this.boksbak = boksbak;
		this.toIfindex = toIfindex;
		calcKey();
	}

	public void setToIfindex(String toIfindex) {
		this.toIfindex = toIfindex;
		calcKey();
	}

	public String hashKey() { return hashKey; }
	private void calcKey() { hashKey = boksbak+":"+toIfindex; }
	public String toString() {
		return "BoksMpBak [boksbak="+boksbak+", toIfindex="+toIfindex+"]";
	}
}
