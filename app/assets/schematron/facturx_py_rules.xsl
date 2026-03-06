<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">

    <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

    <xsl:template match="/">
        <svrl:schematron-output title="Factur-X Python Business Rules (v1.0)" schemaVersion="1.0">
            <xsl:apply-templates select="//rsm:CrossIndustryInvoice"/>
        </svrl:schematron-output>
    </xsl:template>

    <xsl:template match="rsm:CrossIndustryInvoice">

        <!--
            This file provides XSLT 1.0 business rules for the Community ValidationService
            (which uses lxml, not Saxon-HE). These rules are intentionally duplicated from the
            official EN16931 Schematron (XSLT 2.0) to ensure Community edition users get
            basic calculation checks without requiring Java/Saxon.

            The HybridValidationService (Pro) uses the official XSLT via Saxon-HE subprocess
            and does NOT use this file — no double-execution risk.
        -->

        <!-- [BR-FR-01] SIRET Check for French Sellers -->
        <xsl:if test=".//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID = 'FR'">
            <xsl:if test="not(.//ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID[@schemeID='0002']) and not(.//ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID[@schemeID='0009'])">
                <svrl:failed-assert id="BR-FR-01" severity="fatal">
                    <svrl:text>Pour un émetteur français, le SIRET ou SIREN (Identifiant légal) est obligatoire.</svrl:text>
                </svrl:failed-assert>
            </xsl:if>
        </xsl:if>

        <!-- [BR-DE-01] Tax ID Check for German Sellers (Steuernummer or VAT ID) -->
        <xsl:if test=".//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID = 'DE'">
            <xsl:if test="not(.//ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID[@schemeID='FC']) and not(.//ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID[@schemeID='VA'])">
                <svrl:failed-assert id="BR-DE-01" severity="fatal">
                    <svrl:text>Pour un émetteur allemand, le Numéro Fiscal (Steuernummer) ou le Numéro de TVA (Umsatzsteuer-ID) est obligatoire.</svrl:text>
                </svrl:failed-assert>
            </xsl:if>
        </xsl:if>

        <xsl:variable name="sum_lines" select="sum(.//ram:IncludedSupplyChainTradeLineItem/ram:SpecifiedLineTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount)"/>
        <xsl:variable name="net_total" select=".//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:LineTotalAmount"/>

        <!-- [BR-CO-13] Total Amount Check (XSLT 1.0 fallback for Community edition) -->
        <xsl:variable name="diff_lines">
            <xsl:choose>
                <xsl:when test="$sum_lines &gt; $net_total"><xsl:value-of select="$sum_lines - $net_total"/></xsl:when>
                <xsl:otherwise><xsl:value-of select="$net_total - $sum_lines"/></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$diff_lines &gt; 0.01">
            <svrl:failed-assert id="BR-CO-13" severity="fatal">
                <svrl:text>La somme des montants de lignes (<xsl:value-of select="round($sum_lines * 100) div 100"/>) ne correspond pas au total HT déclaré (<xsl:value-of select="$net_total"/>).</svrl:text>
            </svrl:failed-assert>
        </xsl:if>

        <!-- [BR-CO-16] VAT Calculation Check (XSLT 1.0 fallback for Community edition) -->
        <xsl:variable name="tax_basis" select=".//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount"/>
        <xsl:variable name="tax_total" select=".//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount"/>
        <xsl:variable name="grand_total" select=".//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount"/>

        <xsl:variable name="diff_vat">
            <xsl:choose>
                <xsl:when test="($tax_basis + $tax_total) &gt; $grand_total"><xsl:value-of select="($tax_basis + $tax_total) - $grand_total"/></xsl:when>
                <xsl:otherwise><xsl:value-of select="$grand_total - ($tax_basis + $tax_total)"/></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$diff_vat &gt; 0.01">
            <svrl:failed-assert id="BR-CO-16" severity="fatal">
                <svrl:text>Le montant Total TTC (<xsl:value-of select="$grand_total"/>) est incoherent avec la somme du HT (<xsl:value-of select="$tax_basis"/>) et de la TVA (<xsl:value-of select="$tax_total"/>).</svrl:text>
            </svrl:failed-assert>
        </xsl:if>

        <!-- [BR-FR-04] IBAN Check (Warning level) -->
        <xsl:if test="not(.//ram:SpecifiedTradeSettlementPaymentMeans/ram:PayeePartyCreditorFinancialAccount/ram:IBANID)">
            <svrl:failed-assert id="BR-FR-04" severity="warning">
                <svrl:text>Attention : Aucun IBAN n'a été détecté dans les moyens de paiement. La facture pourrait être rejetée par certains portails clients.</svrl:text>
            </svrl:failed-assert>
        </xsl:if>

    </xsl:template>

</xsl:stylesheet>
