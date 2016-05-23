Title: Analysis of vulnerabilities in Juniper's ScreenOS
Date: 2016-5-1 19:38

### Introduction
On the 17th of December 2015, Juniper released a security advisory stating multiple vulnerabilities affecting NetScreen appliances were uncovered during an internal code review **[1]**. Details were vague, raising questions as to why they were only just surfacing when the vulnerabilities had been present as far back as 2012. This paper aims to summarise the actual mechanisms for the vulnerabilities and speculate who planted them.

#### NetScreen OS
Originally developed by NetScreen Technologies and later bought by Juniper, ScreenOS is a proprietary real-time operating system for embedded targets. Unlike the FreeBSD-based Junos used in other products, ScreenOS is unique to the NetScreen product line. NetScreen appliances provide firewall and VPN (virtual private network) functionality for enterprise networks. 

### Firmware analysis
Because Juniper's security advisories do not provide any technical details about the vulnerabilities, it is necessary to do some digging in order to gain any understanding as to their nature. The most obvious method is to study the differences between versions of ScreenOS firmware prior to the security advisory, and the patched version released afterwards. Unfortunately the proprietary nature of ScreenOS means that there is no public source code available, thus to study the differences means analysing the binary firmware files. As binary diffs are hard for humans to analyse, an extra step is required whereby we decompile the machine code instructions into their human-readable assembly counterparts. Juniper uses x86 processors in some of its NetScreen appliances and ARM processors in the rest, so there are actually two different sets of firmware.

While Juniper was quick to release two completely new versions of ScreenOS (6.2.0r19 and 6.3.0r21) that plugged the security holes, they also released patched 'respin' versions (denoted with the 'b' suffix) of existing firmwares, presumably so that customers could deploy the fixes without needing to perform verification testing. These respin versions contain only a minor set of changes, which makes them ideal for comparison with the original versions to see what was changed to fix the security holes, hopefully shedding some light on the mechanisms that gave way to these vulnerabilities and how they might have arisen.

### Administrative access vulnerability
The first vulnerability mentioned in the advisory, CVE-2015-7755, allows unauthorised administrative access in ScreenOS versions 6.3.0r17 to 6.3.0r20. Like most other network appliances, ScreenOS provides both a web interface and a CLI (command-line interface) for remotely managing the device, allowing the user to configure all aspects of the device's operation. For this particular vulnerability we shall analyse the *ssg5ssg20.6.3.0r19.0.bin* file provided in H.D. Moore's GitHub repository **[2]**. In order to analyse the firmware with IDA Pro we must first decompile it using the values listed below:

    Processor type      ARM Big-endian (ARMB)
    =========================================
    Loading address     0x80000               
    File offset         0x20                  
    Loading size        0x2077238             
    ROM start address   0x0                   
    ROM size            0x20F7258             

Because the decompiler output can look quite cryptic, it is a good idea to check the output of the UNIX *strings* utility. *strings* can be used to search binary files for chunks of human-readable text, and is a good starting point for analysis. Given the nature of the vulnerability (unauthorised access) a sensible place to start would be to search for anything relating to authentication, which we can do using the following snippet: `strings -t x ssg5ssg20.6.3.0r19.0.bin | grep "auth"`. Moore's analysis uncovered a group of subroutines related to authentication at address `0x13DAF4` **[3]**. If we study the output of the *strings* command we spot an interesting string, `remote authentication failed for admin user`, preceded by `auth_admin.c`. Using IDA Pro to find references to these strings we stumble upon what is presumably the contents of *auth_admin.c* and the subroutines mentioned in Moore's analysis **[3]**.

A comparison between `sub_13DBEC` in ScreenOS 6.3.0r19 and 6.3.0r19b reveals that several lines of code were removed from this subroutine as part of Juniper's patch (highlighted in red in *Figure 1*) **[3]**. Examining the code, we can see that the pointer loaded into `R1` is used in the resulting call to `sub_ED7D94`. At first glance the string (`<<< \%s(un='\%s') = \%u`) looks like a format string, of which there are several nearby. However jumping to the `sub_ED7D94` subroutine which gets called, reveals what looks to be an implementation of the `strcmp()` function. Depending on the result of `strcmp()`, it either restores the stack and exits the function (if the password supplied by the user matches the magic string), or continues running. Given its location inside an authentication subroutine, this is a deliberate backdoor, and the string was carefully disguised as a formatting string. 

Essentially, the user's credentials are sent to the `auth_admin_internal` function for authentication. If the user supplies `<<< \%s(un='\%s') = \%u` as their password, the function exits immediately and grants full access to the user, bypassing all authentication. This can be verified by initiating an SSH or Telnet session to a vulnerable NetScreen appliance and supplying any username along with the backdoor password.

![Backdoor code removed in ScreenOS 6.3.0r19b highlighted in red]({filename}/images/password_backdoor.png){: class="u-max-full-width" }

*Figure 1: Backdoor code removed in ScreenOS 6.3.0r19b highlighted in red*

Strangely, the backdoor does not occur in versions of ScreenOS prior to 6.3.0r17, thus that it was an intentional modification; though it is not clear who it was made by.

### VPN decryption vulnerability

Juniper's security advisory also mentions a second vulnerability (CVE-2015-7756) that would let an attacker monitor and decrypt VPN traffic. Unlike the remote administration backdoor, this issue affected a larger number of ScreenOS versions: 6.2.0r15 - 6.2.0r18 and 6.3.0r12 - 6.3.0r20 were all vulnerable. Considering the severity of the issue, Juniper's advisory was surprisingly short on details. ScreenOS uses the IPsec protocol to provide securely encrypted VPN functionality. As part of this subsystem, IKE (internet key exchange) is used with Diffie Hellman key exchange to set up a secure session key in order to create an encrypted tunnel between the server and client. 

Once again, it is necessary to turn to firmware disassembly to understand the nature of the vulnerability. Comparing Moore's extracted firmware files, Adam Caudil noticed that a constant (later identified as one of the Weierstraß co-ordinates for the P-256 elliptic curve) was changed in ScreenOS 6.3.0r12, drawing attention towards the random number generation code **[4]**. Using C code from Ralf-Philipp Weinmann's disassembly to create the block diagram in *Figure 2* for the random number generator system, we can see that ScreenOS utilises both Dual_EC_DRBG—a random bit generator based on elliptic curve cryptography, standardised by the NIST (National Institute of Standards and Technology)—and an ANSI X9.31 PRNG **[5]**. The output of this system is used to generate nonces used by IKE for DH key exchange, and so a compromise to this part of the system would have a critical impact on security.

![Diagram of intended method for nonce generation using Dual_EC_DRBG and ANSI X9.31 PRNG]({filename}/images/prng_diagram.png){: class="u-max-full-width" }

*Figure 2: Diagram of intended method for nonce generation using Dual_EC_DRBG and ANSI X9.31 PRNG*

To understand the importance of the change made to the Dual_EC_DRBG Q-point we must first understand the algorithm. Dual_EC_DRBG works by hashing an input seed, running it through an ecliptic curve defined by the points *P* and *Q* to derive a pseudo-random output **[6]**. While it was recommended by NIST, concerns as to its security were raised as far back as 2007 in a CRYPTO talk by Microsoft researchers Dan Shumow and Niels Ferguson. Shumow and Ferguson noted that if the points *P* and *Q* were carefully chosen by an attacker such that `P=eQ`, where *e* is secret, the randomness would be compromised and the attacker could decipher the internal state of the PRNG with only 32 bytes of output **[7]**. It is very difficult for anyone else to find the secret value *e* because of the discrete logarithm problem (which is what makes ecliptic curves so secure in the first place). Thus, only the person who knows *e* may recover the internal state.

After the New York Times reported on internal NSA (National Security Agency) memos leaked by Edward Snowdon, suggesting that the NSA had backdoored the Dual_EC_DRBG algorithm, Juniper released a statement clarifying that ScreenOS did not use the potentially backdoored points specified in the NIST standard **[8]****[9]**; furthermore, the Dual_EC_DRBG output was not used directly, instead it seeded a separate ANSI X9.31 PRNG, the output of which was used by the system for random numbers.

However Willem Pinckaers, another researcher analysing Weinmann's disassembly, noted that contrary to Juniper's statement, a ScreenOS bug meant that the ANSI X9.31 PRNG was completely non-functional **[10]**. Examining the disassembly in *Figure 3*, the `prng_do_reseed()` function (which seeds the ANSI X9.31 PRNG with the Dual_EC_DRBG output) sets `prng_output_idx = 32`, and so the `for` loop is never executed. As both random number generator blocks share the `prng_output_buf` buffer, the end result is that the bits inside the buffer are exclusively generated by Dual_EC_DRBG.

    :::c
    void prng_generate_block(void) {
      // ...
      prng_output_idx = 0;
      ++blocks_generated_since_reseed;
      if (!prng_reseed_not_needed())  // Always 0 by default
        prng_do_reseed();             // Sets prng_output_idx = 32
      for ( ; (unsigned int)prng_output_idx <= 31; prng_output_idx += 8) {
        // Obtain 8 bytes from X9.31
        // Copy to offset in prng_output_buf
      }
    }
*Figure 3: Code snippet of disassembled random number generation by UCSD **[11]***

Knowing that the IKE nonce is exclusively generated from Dual_EC_DRBG, the subtle change to point *Q* in 6.3.0r12 seems much more significant. Putting everything together we can see how VPN traffic decryption is possible:

1. After noticing that the ANSI X9.31 block is non-functional, the *Q* point is modified in secret.
2. Because only the Dual_EC_DRBG block works, the IKE nonce, the DH keys, and thus the session key is non-random.
3. Given that *Q* was chosen such that `P=eQ`, and *e* is only known to the attacker, it is possible that the attacker can compute the session key simply by monitoring a small amount of traffic, thus they are able to decrypt the stream.

As part of the 6.3.0r12b respin, Juniper reversed the *Q* point to its original value, presumably closing up the security hole. Unlike the first backdoor, CVE-2015-7756 could be exploited using entirely passive means, thus it is impossible to tell if this attack was ever executed in the wild.

### Origin of backdoors
While no-one knows with any certainty who planted the backdoors, we can still speculate. The stark difference in sophistication between the backdoors suggests two different sources. While the remote access backdoor is astonishingly simple, the VPN decryption backdoor required both a knowledge of ecliptic curve cryptography and a deep understanding of the ScreenOS code, to the point where the backdoor leverages bugs in Juniper's code that presumably they were not even aware of. While CVE-2015-7756 can only be exploited by the person who changed the *Q* point, CVE-2015-7755 can be exploited by anybody. It seems odd that an attacker would go to such great lengths to ensure only they could exploit one of the backdoors, but leave the other wide open.

On the other hand, `prng_reseed_not_needed` is not always zero. The party who changed the *Q* point could also have added the remote access backdoor in order to ensure ANSI X9.31 was disabled. However implementing two backdoors would drastically increase the risk of being discovered, especially when the remote access vulnerability is so obvious.

If the VPN decryption backdoor was planted with the intention of performing an attack on a specific target then it could be planted by anyone. However, if the intention was mass-surveillance, the resources required would be far greater, thus the backdoor would have to be planted by a nation-state attacker such as the NSA. Supporting the theory that the backdoors originated from different sources, an almost identical copy of the remote access vulnerability was proposed in an issue of Phrack magazine from 2009 **[12]**. 

### Conclusion
Thorough analysis of the firmware changes reveals a wealth of information which was never released by Juniper. While they have committed fixes for both, it is perfectly feasible that there are more undiscovered backdoors. Given the drastic difference in sophistication between the two backdoors, it seems unlikely that they originated from the same source. The complexity of the VPN decryption backdoor and its reliance on signals intelligence for mass-surveillance, suggests that this backdoor was planted by a nation-state attacker outside of Juniper. Assuming that the attacker did not want the backdoor to be detected, it seems unlikely that they would also have planted the remote access backdoor—possibly that originated from a rogue attacker.

Ultimately these revelations raise questions over code review practices, version control security and the relevance of open-source software. One can only wonder how many other widely-used products are affected in this way.

### References

1. [2015-12 Out of Cycle Security Bulletin: ScreenOS: Multiple Security issues with ScreenOS (CVE-2015-7755, CVE-2015-7756)](https://kb.juniper.net/InfoCenter/index?page=content&id=JSA10713&cat=SIRT_1&actp=LIST)
2. [Juniper CVE-2015-7755 and CVE-2015-7756](https://github.com/hdm/juniper-cve-2015-7755)
3. [CVE-2015-7755: Juniper ScreenOS Authentication Backdoor](https://community.rapid7.com/community/infosec/blog/2015/12/20/cve-2015-7755-juniper-screenos-authentication-backdoor)
4. [Much ado about Juniper](https://adamcaudill.com/2015/12/17/much-ado-about-juniper/)
5. [Some analysis of the backdoored backdoor](http://rpw.sh/blog/2015/12/21/the-backdoored-backdoor/)
6. [Dual_Ec_Drbg backdoor: a proof of concept](https://blog.0xbadc0de.be/archives/155)
7. [On the Possibility of a Back Door in the NIST SP800-90 Dual Ec Prng](http://rump2007.cr.yp.to/15-shumow.pdf)
8. [Government Announces Steps to Restore Confidence on Encryption Standards](http://bits.blogs.nytimes.com/2013/09/10/government-announces-steps-to-restore-confidence-on-encryption-standards/?src=twrhp&_r=1)
9. [Juniper Networks product information about Dual_EC_DRBG](https://kb.juniper.net/InfoCenter/index?page=content&id=KB28205&pmv=print&actp=search&searchid=&type=currentpaging)
10. [Willem Pinckaers - Twitter](https://twitter.com/_dvorak_/status/679110950079758336?lang=en-gb)
11. [An update on the backdoor in Juniper's ScreenOS](https://cseweb.ucsd.edu/~hovav/dist/rwc16.pdf)
12. [Netscreen of the Dead: Developing a Trojaned Firmware for Juniper ScreenOS Platforms](http://phrack.org/issues/66/5.html#article)