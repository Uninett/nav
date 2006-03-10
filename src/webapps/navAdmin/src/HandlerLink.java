class HandlerLink
{
	public HandlerLink(String[] Is, Com Icom, int InNum, int InTempNr)
	{
		s = Is;
		com = Icom;
		tempNr = InTempNr;
		num = InNum;
		//PATH = com.getConf().get("ServletPath");
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
			if (s[1].equals("admin"))
			{
				if (linkAdmin()) return;

			}


			// handle functions on this level
			// (admin)
			if (s[1].equals("mailpw"))
			{
				linkMailPw();
			} else
			if (s[1].equals("param"))
			{
				//adminParam();
			} else
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

	/************************************************************
	* Level 2 handler											*
	* link.admin.*												*
	************************************************************/

	private boolean linkAdmin()
	{
		if (s.length >= 3)
		{
			// identify sub-levels


			// handle functions on this level
			if (s[2].equals("get_all"))
			{
				linkAdminGetAll();
				return true;
			}

		}
		return false;
	}

	/************************************************************
	* Level 1 functions											*
	* link.*													*
	************************************************************/

	private void linkMailPw()
	{
		String login = com.getReq().getParameter("login");

		if (login != null)
		{
			com.out(PATH + "?");
			com.out("mailpw=" + login);
		}

	}


	/************************************************************
	* Level 2 functions											*
	* link.admin.*												*
	************************************************************/

	private void linkAdminGetAll()
	{
		com.out(PATH);
		com.out("/AlleOving" + tempNr + ".zip");
		com.out("?");

		com.out("section=" + s[1]);
		com.out("&func=get_all");
	}


	// class vars
	final String PATH;
	String[] s;
	Com com;
	int num;
	int tempNr;

}
