		<h1>
			<center>
				<font color=#000066>
					navAdmin - vlanPlot config - Database config
				</font>
			</center>
		</h1>

		<center>
				<table border="0">
				  <tr>
						<td>
							<b>Velg hva du vil konfigurere</b>
						</td>
					</tr>
				  <tr>
						<td>
						  <b>Nettel</b>

<form method="POST" action="[/main.servletPath]">
  <input type="hidden" name="section" value="vp">
  <input type="hidden" name="func" value="conf">
  <input type="hidden" name="p1" value="database">

  <p><select size="1" name="nettel">
    <option value="alle">All nettel</option>
    <option value="router">Router</option>
    <option value="switch">Switch</option>
    <option value="hub-lan">Hub</option>
  </select></p>
  <p><input type="submit" value="Submit" name="B1"><input type="reset" value="Reset" name="B2"></p>
</form>

						</td>
					</tr>
				  <tr>
						<td>
						  <b>Link</b>

<form method="POST" action="[/main.servletPath]">
  <input type="hidden" name="section" value="vp">
  <input type="hidden" name="func" value="conf">
  <input type="hidden" name="p1" value="database">

  <p>Link fra <select size="1" name="linkFra">
  	<option value="alle">Alle</option>
    <option value="router">Router</option>
    <option value="switch">Switch</option>
    <option value="hub-lan">Hub/Lan</option>
  </select> til <select size="1" name="linkTil">
  	<option value="alle">Alle</option>
    <option value="router">Router</option>
    <option value="switch">Switch</option>
    <option value="hub-lan">Hub/Lan</option>
  </select></p>
  <p><input type="submit" value="Submit" name="B1"><input type="reset" value="Reset" name="B2"></p>
</form>



						</td>
					</tr>

				</table>
		</center>
