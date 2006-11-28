class HandlerLink
{
	public HandlerLink(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		tempNr = InTempNr;
		num = InNum;
		PATH = com.getReq().getContextPath() + com.getReq().getServletPath();
	//}

	//public boolean begin()
	//{

		/************************************************************
		* Level 1 handler											*
		* link.*													*
		************************************************************/

		if (s.length >= 2)
		{
			// identify sub-levels

			// handle functions on this level
			// (admin)
			{
				// default link
				com.out(PATH);
				com.out("?section=" + s[1]);

				if (s.length >= 3)
				{
					com.out("&func=" + s[2]);
				}

				for (int i = 1; i < s.length-2; i++)
				{
					com.out("&p" + i +"=" + s[i+2]);
				}
			}
		} else
		{
			com.out(PATH);
		}
		//return false;
	}

	// class vars
	final String PATH;
	String[] s;
	Com com;
	int num;
	int tempNr;

}
