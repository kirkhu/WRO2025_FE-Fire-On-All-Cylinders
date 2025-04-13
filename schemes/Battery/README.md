<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Battery choice for self-driving cars</div> 
 At last year's international competition, our coach observed that most teams were using 18650 batteries to power their vehicles. He tasked us with comparing the differences between 3S Lithium Polymer (LiPo) and 18650 batteries to determine the optimal battery type for our competition vehicle this year.
### Comparison between 3S Li-Polymer and 18650 Li-ion batteries
  - The following is a comparison of the advantages and disadvantages of 3S Li-Polymer batteries and 18650 Li-ion batteries with the same voltage configuration.
  <table border="1">
    <thead>
      <tr>
      <th>Item</th>
      <th>3S Li-Polymer Battery</th>
      <th>18650 Battery</th>
      </tr>
    </thead>
    <tbody>
      <tr>
      <th>photo</th>
      <td><img src="./img/lipo_battery.png" width="250" alt="lipo_battery "></td>
      <td><img src="./img/18650.png" width="250" alt="18650 "></td>
      </tr>
      <tr>
      <th>Voltage Range</th>
      <td>11.1V (nominal), up to 12.6V (fully charged)</td>
      <td>11.1V (nominal), up to 12.6V (fully charged)</td>
      </tr>
      <tr>
      <th>Energy Density</th>
      <td>Higher energy density compared to the same weight</td>
      <td>Higher capacity per unit volume compared to LiPo</td>
      </tr>
      <tr>
      <th>Weight</th>
      <td>Lighter, good for reducing load</td>
      <td>Relatively heavier</td>
      </tr>
      <tr>
      <th>Output Current</th>
      <td>Supports high discharge rates (C-Rate), can provide high current instantaneously</td>
      <td>Lower discharge rates, suitable for stable power output</td>
      </tr>
      <tr>
      <th>Charging Time</th>
      <td>Supports fast charging but requires a dedicated charger</td>
      <td>Relatively slower charging time</td>
      </tr>
      <tr>
      <th>Safety</th>
      <td>More susceptible to physical damage or overcharging, risk of fire</td>
      <td>Relatively safer, resistant to overcharge and overdischarge</td>
      </tr>
      <tr>
      <th>Shape and Flexibility</th>
      <td>Can be made in various shapes and sizes, high flexibility in fitting space</td>
      <td>Fixed cylindrical shape, less adaptable to different spaces</td>
      </tr>
      <tr>
      <th>Internal Resistance and Efficiency</th>
      <td>Lower internal resistance, suitable for high current discharge, high efficiency</td>
      <td>Relatively higher internal resistance, slightly lower efficiency</td>
      </tr>
      <tr>
      <th>Lifecycle</th>
      <td>Shorter lifespan, fewer charge cycles (typically 300-500 cycles)</td>
      <td>Longer lifespan, more charge cycles (typically 500-1000 cycles)</td>
      </tr>
      <tr>
      <th>Application Scenarios</th>
      <td>Used in drones, RC vehicles, and applications requiring high output</td>
      <td>Used in laptops, power banks, and applications needing stable power supply</td>
      </tr>
      <tr>
      <th>Cost</th>
      <td>Relatively more expensive, requires dedicated charging equipment</td>
      <td>Relatively cheaper</td>
      </tr>
    </tbody>
  </table>

   - As shown in the table above, the 3S Li-Polymer (LiPo) battery has advantages of high output current, high energy density, and a lightweight design, making it particularly suitable for applications that require high instantaneous current, such as drones and RC vehicles. Therefore, we decided to select the __3S Li-Polymer battery (LiPo)__ as the power source for the autonomous vehicle in this competition.
   - Our experience with 3S Li-Po batteries has shown that their safety is a significant concern. Improper charging practices have led to battery fires, and incorrect storage has resulted in battery damage. These incidents underscore the importance of following strict guidelines for handling these batteries.
  <div align=center>
  <table>
  <tr>
  <th>Photo of 3S Li-Polymer (LiPo) battery burnout during charging.</th>
  </tr><tr>
  <td><img src="./img/Burnout.jpg" width="450" alt="battery burnout during charging" align="center" /></td>
  </tr>
  </table>
  </div>

 ### Step-Down power supply Module  Selection
   
   - The working voltage of controllers like the Nvidia Jetson Nano and Raspberry Pi Pico is 5V, while the 3S Li-Polymer battery we selected has a voltage of 12V. Therefore, a 12V to 5V step-down module is needed to reduce the voltage and protect the control board from high voltage damage.

   - Initially, we chose the LM2596 DC-DC adjustable step-down module because it displays output voltage values, which makes monitoring easier and ensures stable voltage throughout the competition. However, the module’s maximum output current is only 3A, which is insufficient for all devices.

   - As a result, we found the 5A Constant Voltage Constant Current Buck Power Supply Module online, with a maximum output current of 5A, which is sufficient to support the normal operation of the autonomous vehicle. Although this module does not have a voltage display function, a battery low-voltage alarm can be used to monitor the battery voltage, ensuring adequate power levels.
  
- #### Step-Down power supply Module Comparison
  <div align="center">
  <table with=100%>
  <tr align="center">
  <th rowspan="2">Photo</th>
  <th> LM2596 DC-DC Adjustable Buck Module LM2596 DC-DC </th>
  <th>5A Constant Voltage Constant Current Buck Power Supply Module ADIO-DC36V5A</th>
  </tr>
  <tr align="center">
  <td><img src="../Power_Supply_System/img/LM25.png" width = "250"  alt="LM25" align=center />  </td>
  <td><img src="../Power_Supply_System/img/ADIO-DC36V5A.png" width = "300"  alt="ADIO-DC36V5A" align=center /> 
  </td>
  </tr>
  <tr >
  <th>Specification</th>
  <td>
  <ol>
    <li>Module Type: Non-isolated Buck (Step-down)</li>
    <li>Input Voltage Range: 3.2V - 40V</li>
    <li>Output Voltage Range: 1.25V - 35V, with a maximum output current of 3A</li>
    <li>Maximum Output Current: 3A</li>
    <li>Voltage Regulation: Input voltage range of 4V - 40V</li>
    <li><a href="https://www.amazon.ae/UIOTEC-Converter-Digital-Step-up-Voltage/dp/B074LX3YYT" target="_blank">website</a> </li>
    </ol>
   </td>
   <td>
   <ol>
    <li>Input Voltage Range: 4 - 38V</li>
    <li>Output Voltage Range: 1.25 - 36V, continuously adjustable</li>
    <li>Output Current Range: Adjustable, maximum of 5A</li>   
    <li><a href="https://shop.cpu.com.tw/product/57434/info/" target="_blank">website</a></li>
    </ol>
    </td>
    </tr>
    </table>
    </div>
 
### Charging/Discharging Equipment and Li-Polymer Battery Low Voltage Alarm.
  - To protect the 3S Li-Polymer (LiPo) battery from damage during use and storage and to extend its lifespan, we implemented the following strategies:
    - __Use a Dedicated Charger:__ Choose a balanced charger suitable for LiPo batteries to ensure each cell’s voltage remains balanced, preventing damage due to overcharging or unbalanced charging.
    <div align="center">
    <table>
    <tr align="center">
    <th colspan="3">Dedicated Charger(Charging/Discharging Equipment)</th>
    </tr>
    <tr align="center">
    <th>Skyrc E430</th>
    <th>Skyrc Imax B6C2 v2</th>
    <th>HOTA D6 Pro</th>
    </tr>
    <tr>
    <td><img src="./img/e430.png" width = "300"    /></td>
    <td><img src="./img/B6AC2.png" width = "300"  /></td>
    <td><img src="./img/HOTA.png" width = "300"  /></td> 
     </tr>
     </table>
     </div>      

    - __Monitor the Charging Process:__ Supervise the battery during charging, avoiding extended periods without monitoring to quickly detect and resolve any charging abnormalities.

    - __Control Charging Voltage and Current:__ Keep the charging voltage below the standard 4.2V per cell and maintain an appropriate charging current to prevent damage from fast charging.

    - __Avoid Over-Discharge:__ During use, ensure each cell’s voltage does not drop below 3.0V to prevent over-discharge, which could damage the battery and reduce its lifespan.

    - __Safe Storage:__ When not in use, store the battery in a fireproof bag or a dedicated safety container to avoid damage from external pressure or high temperatures.

    - __Storage Voltage:__ For long-term storage, charge the battery to around 50% (3.7V-3.85V per cell) to extend its lifespan and reduce the risk of self-discharge.

    - __Keep Away from High Temperatures:__ Avoid using or storing the battery in high-temperature environments, as heat accelerates aging and increases the risk of damage and fire.

    - __Regular Battery Checks:__ Inspect the battery regularly for appearance and voltage. If swelling, cracking, or voltage abnormalities are detected, immediately stop using and dispose of it safely.

  - #### Low Voltage Alarm       
      
      <div align="center">
       <table>
       <th colspan="2">Li-Polymer Battery Low Voltage Alarm </th>
       <tr>
       <td>Installing a low-voltage alarm on the battery can emit an audible warning when the voltage falls below a set value, alerting the user to monitor or replace the battery in time. This effectively prevents insufficient power issues during competitions and protects the battery from damage due to over-discharge.</td>
        <td><img src="./img/low_voltage_alarm.png" width = "400"  alt="low_voltage_alarm" align="center" /></td>
       </tr>
       </table>
       </div>
     
 
# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
