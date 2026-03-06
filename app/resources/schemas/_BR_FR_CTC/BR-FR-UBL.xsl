<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<xsl:stylesheet xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                xmlns:cn="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
                xmlns:custom="http://www.example.org/custom"
                xmlns:oxy="http://www.oxygenxml.com/schematron/validation"
                xmlns:saxon="http://saxon.sf.net/"
                xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="2.0"
                xml:base="file:/Users/cyrille/Documents/_Cyrille_Boulot/ADMAREL_2025/_FNFE_2025/_Commission_AFNOR/_REVUE_OCTOBRE/_XP_Z12_012/_Schematron/_FINAL/_A%20PUBLIER/2025_11_14_FNFE_SCHEMATRONS_FR_CTC_V1.2.1/20251114_BR-FR-Flux2-Schematron-UBL_V1.2.0.sch_xslt_cascade"><!--Implementers: please note that overriding process-prolog or process-root is 
    the preferred method for meta-stylesheets to use where possible. -->
   <xsl:param name="archiveDirParameter"/>
   <xsl:param name="archiveNameParameter"/>
   <xsl:param name="fileNameParameter"/>
   <xsl:param name="fileDirParameter"/>
   <xsl:variable name="document-uri">
      <xsl:value-of select="document-uri(/)"/>
   </xsl:variable>
   <!--PHASES-->
   <!--PROLOG-->
   <xsl:output xmlns:iso="http://purl.oclc.org/dsdl/schematron" method="xml"/>
   <!--XSD TYPES FOR XSLT2-->
   <!--KEYS AND FUNCTIONS-->
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-id-format"
                 as="xs:boolean">
      <xsl:param name="id" as="xs:string?"/>
      <xsl:sequence select="       matches(normalize-space($id), '^[A-Za-z0-9+\-_/]+$') and       not(matches($id, ' ')) and       not(starts-with($id, ' ')) and       not(ends-with($id, ' '))       "/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-date-format"
                 as="xs:boolean">
      <xsl:param name="date" as="xs:string?"/>
      <!-- Vérifie le format AAAA-MM-JJ -->
      <xsl:variable name="isFormatValid"
                    select="matches($date, '^20\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$')"/>
      <!-- Extraction des composantes -->
      <xsl:variable name="year" select="number(substring($date, 1, 4))"/>
      <xsl:variable name="month" select="number(substring($date, 6, 2))"/>
      <xsl:variable name="day" select="number(substring($date, 9, 2))"/>
      <!-- Calcul année bissextile -->
      <xsl:variable name="isLeapYear"
                    select="($year mod 4 = 0 and $year mod 100 != 0) or ($year mod 400 = 0)"/>
      <!-- Nombre de jours max selon le mois -->
      <xsl:variable name="maxDay"
                    select="       if ($month = (1, 3, 5, 7, 8, 10, 12)) then 31       else if ($month = (4, 6, 9, 11)) then 30       else if ($month = 2 and $isLeapYear) then 29       else if ($month = 2) then 28       else 0"/>
      <!-- Résultat final -->
      <xsl:sequence select="$isFormatValid and $day le $maxDay"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-document-type-code"
                 as="xs:boolean">
      <xsl:param name="code" as="xs:string?"/>
      <xsl:variable name="custom:document-type-codes"
                    as="xs:string"
                    select="'380 389 393 501 386 500 384 471 472 473 261 262 381 396 502 503'"/>
      <xsl:sequence select="$code = tokenize($custom:document-type-codes, '\s+')"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-billing-mode"
                 as="xs:boolean">
      <xsl:param name="code" as="xs:string?"/>
      <xsl:variable name="custom:billing-modes"
                    as="xs:string"
                    select="'B1 S1 M1 B2 S2 M2 S3 B4 S4 M4 S5 S6 B7 S7 B8 S8 M8'"/>
      <xsl:sequence select="$code = tokenize($custom:billing-modes, '\s+')"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:check-siret-siren-coherence"
                 as="xs:boolean">
      <xsl:param name="siret" as="xs:string?"/>
      <xsl:param name="siren" as="xs:string?"/>
      <xsl:sequence select="matches($siret, '^\d{14}$') and substring($siret, 1, 9) = $siren"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-bar-treatment"
                 as="xs:boolean">
      <xsl:param name="value" as="xs:string?"/>
      <xsl:sequence select="$value = ('B2B', 'B2BINT', 'B2C', 'OUTOFSCOPE', 'ARCHIVEONLY')"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-eas-code"
                 as="xs:boolean">
      <xsl:param name="code" as="xs:string?"/>
      <xsl:variable name="custom:eas-codes"
                    as="xs:string"
                    select="'AN AQ AS AU EM 0002 0007 0009 0037 0060 0088 0096 0097 0106        0130 0135 0142 0147 0151 0154 0158 0170 0177 0183 0184 0188 0190        0191 0192 0193 0194 0195 0196 0198 0199 0200 0201 0202 0203 0204        0205 0208 0209 0210 0211 0212 0213 0215 0216 0217 0218 0221 0225        0230 0235 0240 9910 9913 9914 9915 9918 9919 9920 9922 9923 9924        9925 9926 9927 9928 9929 9930 9931 9932 9933 9934 9935 9936 9937        9938 9939 9940 9941 9942 9943 9944 9945 9946 9947 9948 9949 9950        9951 9952 9953 9957 9959'"/>
      <xsl:sequence select="$code = tokenize($custom:eas-codes, '\s+')"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-vat-category-code"
                 as="xs:boolean">
      <xsl:param name="code" as="xs:string?"/>
      <xsl:variable name="validCodes" select="('S', 'E', 'AE', 'K', 'G', 'O', 'Z')"/>
      <xsl:sequence select="$code = $validCodes"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-vat-rate"
                 as="xs:boolean">
      <xsl:param name="rate" as="xs:string?"/>
      <xsl:variable name="validRates"
                    select="(       '0', '0.0', '0.00', '10', '10.0', '10.00', '13', '13.0', '13.00', '20', '20.0', '20.00',       '8.5', '8.50', '19.6', '19.60', '2.1', '2.10', '5.5', '5.50', '7', '7.0', '7.00',       '20.6', '20.60', '1.05', '0.9', '0.90', '1.75', '9.2', '9.20', '9.6', '9.60'       )"/>
      <xsl:sequence select="$rate = $validRates"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-attachment-code"
                 as="xs:boolean">
      <xsl:param name="code" as="xs:string?"/>
      <xsl:variable name="validCodes"
                    select="(       'RIB', 'LISIBLE', 'FEUILLE_DE_STYLE', 'PJA', 'BORDEREAU_SUIVI',       'DOCUMENT_ANNEXE', 'BON_LIVRAISON', 'BON_COMMANDE',       'BORDEREAU_SUIVI_VALIDATION', 'ETAT_ACOMPTE', 'FACTURE_PAIEMENT_DIRECT'       )"/>
      <xsl:sequence select="$code = $validCodes"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-schemeid-format"
                 as="xs:boolean">
      <xsl:param name="value" as="xs:string?"/>
      <!-- Autorise lettres, chiffres, + - _ / sans espaces -->
      <xsl:sequence select="matches($value, '^[A-Za-z0-9+\-_/]+$')"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-decimal-19-2"
                 as="xs:boolean">
      <xsl:param name="amount" as="xs:string?"/>
      <xsl:sequence select="matches($amount, '^[-]?\d{1,19}(\.\d{1,2})?$') and string-length(replace($amount, '\.', '')) le 19"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-decimal-19-4"
                 as="xs:boolean">
      <xsl:param name="quantity" as="xs:string?"/>
      <xsl:sequence select="matches($quantity, '^[-]?\d{1,19}(\.\d{1,4})?$') and string-length(replace($quantity, '\.', '')) le 19"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-decimal-19-6-positive"
                 as="xs:boolean">
      <xsl:param name="amount" as="xs:string?"/>
      <xsl:sequence select="matches($amount, '^\d{1,19}(\.\d{1,6})?$') and string-length(replace($amount, '\.', '')) le 19"/>
   </xsl:function>
   <xsl:function xmlns="http://purl.oclc.org/dsdl/schematron"
                 name="custom:is-valid-percent-4-2-positive"
                 as="xs:boolean">
      <xsl:param name="percent" as="xs:string?"/>
      <xsl:sequence select="matches($percent, '^\d{1,4}(\.\d{1,2})?$') and string-length(replace($percent, '\.', '')) le 4"/>
   </xsl:function>
   <!--DEFAULT RULES-->
   <!--MODE: SCHEMATRON-SELECT-FULL-PATH-->
   <!--This mode can be used to generate an ugly though full XPath for locators-->
   <xsl:template match="*" mode="schematron-select-full-path">
      <xsl:apply-templates select="." mode="schematron-get-full-path"/>
   </xsl:template>
   <!--MODE: SCHEMATRON-FULL-PATH-->
   <!--This mode can be used to generate an ugly though full XPath for locators-->
   <xsl:template match="*" mode="schematron-get-full-path">
      <xsl:variable name="sameUri">
         <xsl:value-of select="saxon:system-id() = parent::node()/saxon:system-id()"
                       use-when="function-available('saxon:system-id')"/>
         <xsl:value-of select="oxy:system-id(.) = oxy:system-id(parent::node())"
                       use-when="not(function-available('saxon:system-id')) and function-available('oxy:system-id')"/>
         <xsl:value-of select="true()"
                       use-when="not(function-available('saxon:system-id')) and not(function-available('oxy:system-id'))"/>
      </xsl:variable>
      <xsl:if test="$sameUri = 'true'">
         <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      </xsl:if>
      <xsl:text>/</xsl:text>
      <xsl:choose>
         <xsl:when test="namespace-uri()=''">
            <xsl:value-of select="name()"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:text>*:</xsl:text>
            <xsl:value-of select="local-name()"/>
            <xsl:text>[namespace-uri()='</xsl:text>
            <xsl:value-of select="namespace-uri()"/>
            <xsl:text>']</xsl:text>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="$sameUri = 'true'">
         <xsl:variable name="preceding"
                       select="count(preceding-sibling::*[local-name()=local-name(current())       and namespace-uri() = namespace-uri(current())])"/>
         <xsl:text>[</xsl:text>
         <xsl:value-of select="1+ $preceding"/>
         <xsl:text>]</xsl:text>
      </xsl:if>
   </xsl:template>
   <xsl:template match="@*" mode="schematron-get-full-path">
      <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      <xsl:text>/</xsl:text>
      <xsl:choose>
         <xsl:when test="namespace-uri()=''">@<xsl:value-of select="name()"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:text>@*[local-name()='</xsl:text>
            <xsl:value-of select="local-name()"/>
            <xsl:text>' and namespace-uri()='</xsl:text>
            <xsl:value-of select="namespace-uri()"/>
            <xsl:text>']</xsl:text>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="text()" mode="schematron-get-full-path">
      <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      <xsl:text>/</xsl:text>
      <xsl:text>text()</xsl:text>
      <xsl:variable name="preceding" select="count(preceding-sibling::text())"/>
      <xsl:text>[</xsl:text>
      <xsl:value-of select="1+ $preceding"/>
      <xsl:text>]</xsl:text>
   </xsl:template>
   <xsl:template match="comment()" mode="schematron-get-full-path">
      <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      <xsl:text>/</xsl:text>
      <xsl:text>comment()</xsl:text>
      <xsl:variable name="preceding" select="count(preceding-sibling::comment())"/>
      <xsl:text>[</xsl:text>
      <xsl:value-of select="1+ $preceding"/>
      <xsl:text>]</xsl:text>
   </xsl:template>
   <xsl:template match="processing-instruction()" mode="schematron-get-full-path">
      <xsl:apply-templates select="parent::*" mode="schematron-get-full-path"/>
      <xsl:text>/</xsl:text>
      <xsl:text>processing-instruction()</xsl:text>
      <xsl:variable name="preceding"
                    select="count(preceding-sibling::processing-instruction())"/>
      <xsl:text>[</xsl:text>
      <xsl:value-of select="1+ $preceding"/>
      <xsl:text>]</xsl:text>
   </xsl:template>
   <!--MODE: SCHEMATRON-FULL-PATH-2-->
   <!--This mode can be used to generate prefixed XPath for humans-->
   <xsl:template match="node() | @*" mode="schematron-get-full-path-2">
      <xsl:for-each select="ancestor-or-self::*">
         <xsl:text>/</xsl:text>
         <xsl:value-of select="name(.)"/>
         <xsl:if test="preceding-sibling::*[name(.)=name(current())]">
            <xsl:text>[</xsl:text>
            <xsl:value-of select="count(preceding-sibling::*[name(.)=name(current())])+1"/>
            <xsl:text>]</xsl:text>
         </xsl:if>
      </xsl:for-each>
      <xsl:if test="not(self::*)">
         <xsl:text/>/@<xsl:value-of select="name(.)"/>
      </xsl:if>
   </xsl:template>
   <!--MODE: SCHEMATRON-FULL-PATH-3-->
   <!--This mode can be used to generate prefixed XPath for humans 
	(Top-level element has index)-->
   <xsl:template match="node() | @*" mode="schematron-get-full-path-3">
      <xsl:for-each select="ancestor-or-self::*">
         <xsl:text>/</xsl:text>
         <xsl:value-of select="name(.)"/>
         <xsl:if test="parent::*">
            <xsl:text>[</xsl:text>
            <xsl:value-of select="count(preceding-sibling::*[name(.)=name(current())])+1"/>
            <xsl:text>]</xsl:text>
         </xsl:if>
      </xsl:for-each>
      <xsl:if test="not(self::*)">
         <xsl:text/>/@<xsl:value-of select="name(.)"/>
      </xsl:if>
   </xsl:template>
   <!--MODE: GENERATE-ID-FROM-PATH -->
   <xsl:template match="/" mode="generate-id-from-path"/>
   <xsl:template match="text()" mode="generate-id-from-path">
      <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
      <xsl:value-of select="concat('.text-', 1+count(preceding-sibling::text()), '-')"/>
   </xsl:template>
   <xsl:template match="comment()" mode="generate-id-from-path">
      <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
      <xsl:value-of select="concat('.comment-', 1+count(preceding-sibling::comment()), '-')"/>
   </xsl:template>
   <xsl:template match="processing-instruction()" mode="generate-id-from-path">
      <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
      <xsl:value-of select="concat('.processing-instruction-', 1+count(preceding-sibling::processing-instruction()), '-')"/>
   </xsl:template>
   <xsl:template match="@*" mode="generate-id-from-path">
      <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
      <xsl:value-of select="concat('.@', name())"/>
   </xsl:template>
   <xsl:template match="*" mode="generate-id-from-path" priority="-0.5">
      <xsl:apply-templates select="parent::*" mode="generate-id-from-path"/>
      <xsl:text>.</xsl:text>
      <xsl:value-of select="concat('.',name(),'-',1+count(preceding-sibling::*[name()=name(current())]),'-')"/>
   </xsl:template>
   <!--MODE: GENERATE-ID-2 -->
   <xsl:template match="/" mode="generate-id-2">U</xsl:template>
   <xsl:template match="*" mode="generate-id-2" priority="2">
      <xsl:text>U</xsl:text>
      <xsl:number level="multiple" count="*"/>
   </xsl:template>
   <xsl:template match="node()" mode="generate-id-2">
      <xsl:text>U.</xsl:text>
      <xsl:number level="multiple" count="*"/>
      <xsl:text>n</xsl:text>
      <xsl:number count="node()"/>
   </xsl:template>
   <xsl:template match="@*" mode="generate-id-2">
      <xsl:text>U.</xsl:text>
      <xsl:number level="multiple" count="*"/>
      <xsl:text>_</xsl:text>
      <xsl:value-of select="string-length(local-name(.))"/>
      <xsl:text>_</xsl:text>
      <xsl:value-of select="translate(name(),':','.')"/>
   </xsl:template>
   <!--Strip characters-->
   <xsl:template match="text()" priority="-1"/>
   <!--SCHEMA SETUP-->
   <xsl:template match="/">
      <xsl:apply-templates select="/" mode="M20"/>
      <xsl:apply-templates select="/" mode="M21"/>
      <xsl:apply-templates select="/" mode="M22"/>
      <xsl:apply-templates select="/" mode="M23"/>
      <xsl:apply-templates select="/" mode="M24"/>
      <xsl:apply-templates select="/" mode="M25"/>
      <xsl:apply-templates select="/" mode="M26"/>
      <xsl:apply-templates select="/" mode="M27"/>
      <xsl:apply-templates select="/" mode="M28"/>
      <xsl:apply-templates select="/" mode="M29"/>
      <xsl:apply-templates select="/" mode="M30"/>
      <xsl:apply-templates select="/" mode="M31"/>
      <xsl:apply-templates select="/" mode="M32"/>
      <xsl:apply-templates select="/" mode="M33"/>
      <xsl:apply-templates select="/" mode="M34"/>
      <xsl:apply-templates select="/" mode="M35"/>
      <xsl:apply-templates select="/" mode="M36"/>
      <xsl:apply-templates select="/" mode="M37"/>
      <xsl:apply-templates select="/" mode="M38"/>
      <xsl:apply-templates select="/" mode="M39"/>
      <xsl:apply-templates select="/" mode="M40"/>
      <xsl:apply-templates select="/" mode="M41"/>
      <xsl:apply-templates select="/" mode="M42"/>
      <xsl:apply-templates select="/" mode="M43"/>
      <xsl:apply-templates select="/" mode="M44"/>
      <xsl:apply-templates select="/" mode="M45"/>
      <xsl:apply-templates select="/" mode="M46"/>
      <xsl:apply-templates select="/" mode="M47"/>
      <xsl:apply-templates select="/" mode="M48"/>
      <xsl:apply-templates select="/" mode="M49"/>
      <xsl:apply-templates select="/" mode="M50"/>
      <xsl:apply-templates select="/" mode="M51"/>
      <xsl:apply-templates select="/" mode="M52"/>
      <xsl:apply-templates select="/" mode="M53"/>
      <xsl:apply-templates select="/" mode="M54"/>
      <xsl:apply-templates select="/" mode="M55"/>
      <xsl:apply-templates select="/" mode="M56"/>
      <xsl:apply-templates select="/" mode="M57"/>
      <xsl:apply-templates select="/" mode="M58"/>
      <xsl:apply-templates select="/" mode="M59"/>
      <xsl:apply-templates select="/" mode="M60"/>
      <xsl:apply-templates select="/" mode="M61"/>
   </xsl:template>
   <!--SCHEMATRON PATTERNS-->
   <!--PATTERN BR-FR-01BR-FR-01 — Validation de la longueur et du format des identifiants de facture-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:ID | cn:CreditNote/cbc:ID"
                 priority="1002"
                 mode="M20">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 35"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/BT-1 : L'identifiant de facture (cbc:ID) ne doit pas dépasser 35 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier que l'identifiant respecte cette limite. </xsl:text>
               <xsl:text>
ID:BR-FR-01_BT-1-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/BT-1 : L'identifiant de facture (cbc:ID) contient des caractères non autorisés. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles + - _ / sont autorisés, sans espaces. </xsl:text>
               <xsl:text>
ID:BR-FR-01_BT-1-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M20"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID | cn:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID"
                 priority="1001"
                 mode="M20">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 35"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/BT-25 : L'identifiant de facture référencée (cbc:ID) ne doit pas dépasser 35 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier que l'identifiant respecte cette limite. </xsl:text>
               <xsl:text>
ID:BR-FR-01_BT-25-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/BT-25 : L'identifiant de facture référencée (cbc:ID) contient des caractères non autorisés. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles + - _ / sont autorisés, sans espaces. </xsl:text>
               <xsl:text>
ID:BR-FR-01_BT-25-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M20"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:BillingReference/cac:DocumentReference/cbc:ID | cn:CreditNote/cac:CreditNoteLine/cac:BillingReference/cac:DocumentReference/cbc:ID"
                 priority="1000"
                 mode="M20">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 35"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/EXT-FR-FE-136 : L'identifiant de facture référencée en ligne (cbc:ID) ne doit pas dépasser 35 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier que l'identifiant respecte cette limite. </xsl:text>
               <xsl:text>
ID:BR-FR-01_EXT-FR-FE-136-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-01/EXT-FR-FE-136 : L'identifiant de facture référencée en ligne (cbc:ID) contient des caractères non autorisés. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles + - _ / sont autorisés, sans espaces. </xsl:text>
               <xsl:text>
ID:BR-FR-01_BT-EXT-FR-FE-136-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M20"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M20"/>
   <xsl:template match="@*|node()" priority="-2" mode="M20">
      <xsl:apply-templates select="@*|*" mode="M20"/>
   </xsl:template>
   <!--PATTERN BR-FR-02BR-FR-02 — Validation du format des identifiants de facture-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:ID | cn:CreditNote/cbc:ID"
                 priority="1002"
                 mode="M21">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-02/BT-1 : L'identifiant de facture (cbc:ID) doit être composé uniquement de caractères alphanumériques (A-Z, a-z, 0-9) et peut contenir les caractères spéciaux autorisés : tiret (-), plus (+), tiret bas (_), barre oblique (/). Il ne doit pas contenir uniquement des espaces, ni commencer ou se terminer par un espace, ni contenir d'espaces consécutifs. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez corriger le format de l'identifiant. </xsl:text>
               <xsl:text>
ID:BR-FR-02_BT-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M21"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID | cn:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID"
                 priority="1001"
                 mode="M21">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-02/BT-25 : L'identifiant de facture référencée (cbc:ID) doit respecter le format autorisé : caractères alphanumériques et les symboles - + _ /. Il ne doit pas contenir uniquement des espaces, ni commencer ou se terminer par un espace, ni contenir d'espaces consécutifs. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez corriger le format de l'identifiant. </xsl:text>
               <xsl:text>
ID:BR-FR-02_BT-25</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M21"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:DocumentReference/cbc:ID | cn:CreditNote/cac:CreditNoteLine/cac:DocumentReference/cbc:ID"
                 priority="1000"
                 mode="M21">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-id-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> EXT-FR-FE-136 : L'identifiant de facture référencée en ligne (cbc:ID) doit respecter le format autorisé : caractères alphanumériques et les symboles - + _ /. Il ne doit pas contenir uniquement des espaces, ni commencer ou se terminer par un espace, ni contenir d'espaces consécutifs. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez corriger le format de l'identifiant. </xsl:text>
               <xsl:text>
ID:BR-FR-02_EXT-FR-FE-136</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M21"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M21"/>
   <xsl:template match="@*|node()" priority="-2" mode="M21">
      <xsl:apply-templates select="@*|*" mode="M21"/>
   </xsl:template>
   <!--PATTERN BR-FR-03BR-FR-03 — Validation de l'année dans les dates (2000–2099)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:IssueDate | cn:CreditNote/cbc:IssueDate"
                 priority="1010"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-2 : La date d’émission doit contenir une année comprise entre 2000 et 2099, au format AAAAMMJJ. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier que l’année est correcte et que le format est conforme. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:TaxPointDate | cn:CreditNote/cbc:TaxPointDate"
                 priority="1009"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-7 : La date de fait générateur de la taxe doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-7</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:DueDate | cn:CreditNote/cbc:DueDate"
                 priority="1008"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-9 : La date d’échéance doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-9</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:BillingReference/cac:InvoiceDocumentReference/cbc:IssueDate | cn:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:IssueDate"
                 priority="1007"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-26 : La date d’émission de la facture référencée doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-26</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Delivery/cbc:ActualDeliveryDate | cn:CreditNote/cac:Delivery/cbc:ActualDeliveryDate"
                 priority="1006"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-72 : La date de livraison effective doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-72</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoicePeriod/cbc:StartDate | cn:CreditNote/cac:InvoicePeriod/cbc:StartDate"
                 priority="1005"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-73 : La date de début de période de facturation doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-73</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoicePeriod/cbc:EndDate | cn:CreditNote/cac:InvoicePeriod/cbc:EndDate"
                 priority="1004"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-74 : La date de fin de période de facturation doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-74</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:DocumentReference/cbc:IssueDate | cn:CreditNote/cac:CreditNoteLine/cac:DocumentReference/cbc:IssueDate"
                 priority="1003"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> EXT-FR-FE-138 : La date d’émission de la facture référencée en ligne doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_EXT-FR-FE-138</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:Delivery/cbc:ActualDeliveryDate | cn:CreditNote/cac:CreditNoteLine/cac:Delivery/cbc:ActualDeliveryDate"
                 priority="1002"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> EXT-FR-FE-158 : La date de livraison effective en ligne doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_EXT-FR-FE-158</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:InvoicePeriod/cbc:StartDate | cn:CreditNote/cac:CreditNoteLine/cac:InvoicePeriod/cbc:StartDate"
                 priority="1001"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-134 : La date de début de période de facturation en ligne doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-134</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:InvoicePeriod/cbc:EndDate | cn:CreditNote/cac:CreditNoteLine/cac:InvoicePeriod/cbc:EndDate"
                 priority="1000"
                 mode="M22">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-date-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-03/BT-135 : La date de fin de période de facturation en ligne doit contenir une année entre 2000 et 2099. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez vérifier la validité de la date. </xsl:text>
               <xsl:text>
ID:BR-FR-03_BT-135</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M22"/>
   <xsl:template match="@*|node()" priority="-2" mode="M22">
      <xsl:apply-templates select="@*|*" mode="M22"/>
   </xsl:template>
   <!--PATTERN BR-FR-04BR-FR-04 — Validation du code type de document-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:InvoiceTypeCode | cn:CreditNote/cbc:CreditNoteTypeCode"
                 priority="1002"
                 mode="M23">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test=". = ('380','389','393','501','386','500','384','471','472','473','261','262','381','396','502','503')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-04/BT-3 : Le code type de document (cbc:InvoiceTypeCode") n’est pas autorisé. Valeurs acceptées : 380, 389, 393, 501, 386, 500, 384, 471, 472, 473, 261, 262, 381, 396, 502, 503. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code conforme à la liste autorisée. Les autres codes définis dans la norme UNTDID 1001 ne doivent pas être utilisés. </xsl:text>
               <xsl:text>
ID:BR-FR-04_BT-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M23"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:BillingReference/cac:InvoiceDocumentReference/cbc:DocumentTypeCode | cn:CreditNote/cac:BillingReference/cac:InvoiceDocumentReference/cbc:DocumentTypeCode"
                 priority="1001"
                 mode="M23">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test=". = ('380','389','393','501','386','500','384','471','472','473','261','262','381','396','502','503')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-04/EXT-FR-FE-02 : Le code type de document référencé (cbc:DocumentTypeCode) n’est pas autorisé. Valeurs acceptées : 380, 389, 393, 501, 386, 500, 384, 471, 472, 473, 261, 262, 381, 396, 502, 503. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code conforme à la liste autorisée. </xsl:text>
               <xsl:text>
ID:BR-FR-04_EXT-FR-FE-02</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M23"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:BillingReference/cac:InvoiceDocumentReference/cbc:DocumentTypeCode | cn:CreditNote/cac:CreditNoteLine/cac:BillingReference/cac:InvoiceDocumentReference/cbc:DocumentTypeCode"
                 priority="1000"
                 mode="M23">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test=". = ('380','389','393','501','386','500','384','471','472','473','261','262','381','396','502','503')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-04/EXT-FR-FE-137 : Le code type de document référencé en ligne (cbc:DocumentTypeCode) n’est pas autorisé. Valeurs acceptées : 380, 389, 393, 501, 386, 500, 384, 471, 472, 473, 261, 262, 381, 396, 502, 503. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code conforme à la liste autorisée. </xsl:text>
               <xsl:text>
ID:BR-FR-04_EXT-FR-FE-137</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M23"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M23"/>
   <xsl:template match="@*|node()" priority="-2" mode="M23">
      <xsl:apply-templates select="@*|*" mode="M23"/>
   </xsl:template>
   <!--PATTERN BR-FR-05BR-FR-05 — Présence obligatoire des mentions légales dans les notes (BG-3)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M24">
      <xsl:variable name="allNotes" select="string-join(./cbc:Note, '')"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="contains($allNotes, '#PMT#')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-05/BT-22 : La mention relative aux frais de recouvrement (code PMT) est absente. Elle est obligatoire dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-05_BT-22-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="contains($allNotes, '#PMD#')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-05/BT-22 : La mention relative aux pénalités de retard (code PMD) est absente. Elle est obligatoire dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-05_BT-22-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="contains($allNotes, '#AAB#')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-05/BT-22 : La mention relative à l’escompte ou à son absence (code AAB) est absente. Elle est obligatoire dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-05_BT-22-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M24"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M24"/>
   <xsl:template match="@*|node()" priority="-2" mode="M24">
      <xsl:apply-templates select="@*|*" mode="M24"/>
   </xsl:template>
   <!--PATTERN BR-FR-06BR-FR-06 — Unicité des codes sujets dans les notes (BG-3)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M25">
      <xsl:variable name="allNotes" select="string-join(./cbc:Note, '')"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(tokenize($allNotes, '#PMT#')) - 1  le 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-06/BT-21 : Le code sujet PMT (indemnité forfaitaire pour frais de recouvrement) ne doit apparaître qu'une seule fois dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-06_BT-21-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(tokenize($allNotes, '#PMD#')) - 1  le 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-06/BT-21 : Le code sujet PMD (pénalités de retard) ne doit apparaître qu'une seule fois dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-06_BT-21-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(tokenize($allNotes, '#AAB#')) - 1  le 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-06/BT-21 : Le code sujet AAB (mention d’escompte ou d’absence d’escompte) ne doit apparaître qu'une seule fois dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-06_BT-21-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(tokenize($allNotes, '#TXD#')) - 1  le 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-06/BT-21 : Le code sujet TXD (mention de taxe) ne doit apparaître qu'une seule fois dans les notes (BG-3). </xsl:text>
               <xsl:text>
ID:BR-FR-06_BT-21-4</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M25"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M25"/>
   <xsl:template match="@*|node()" priority="-2" mode="M25">
      <xsl:apply-templates select="@*|*" mode="M25"/>
   </xsl:template>
   <!--PATTERN BR-FR-08BR-FR-08 — Validation du mode de facturation (BT-23)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cbc:ProfileID | cn:CreditNote/cbc:ProfileID"
                 priority="1000"
                 mode="M26">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-billing-mode(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-08/BT-23 : La valeur du mode de facturation (ram:ID) n’est pas autorisée. Valeurs acceptées : B1, S1, M1, B2, S2, M2, B4, S4, M4, S5, S6, B7, S7. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser une valeur conforme à la liste des modes de facturation autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-08_BT-23</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M26"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M26"/>
   <xsl:template match="@*|node()" priority="-2" mode="M26">
      <xsl:apply-templates select="@*|*" mode="M26"/>
   </xsl:template>
   <!--PATTERN BR-FR-09BR-FR-09 — Cohérence entre SIRET (ID avec schemeId = 0009) et SIREN (Legal ID)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party | cn:CreditNote/cac:AccountingSupplierParty/cac:Party"
                 priority="1009"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002']"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/BT-29 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_BT-29</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party | cn:CreditNote/cac:AccountingCustomerParty/cac:Party"
                 priority="1008"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002']"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/BT-46 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_BT-46</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PayeeParty | cn:CreditNote/cac:PayeeParty"
                 priority="1007"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/BT-60 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_BT-60</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:AgentParty | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:AgentParty"
                 priority="1006"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-06 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-06</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty | cn:CreditNote/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty"
                 priority="1005"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-46 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-46</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:AgentParty | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:AgentParty"
                 priority="1004"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-69 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-69</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party"
                 priority="1003"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-92 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-92</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party"
                 priority="1002"
                 mode="M27">
      <xsl:variable name="siret" select="cac:PartyIdentification/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-115 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-115</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Delivery | cn:CreditNote/cac:Delivery"
                 priority="1001"
                 mode="M27">
      <xsl:variable name="siret" select="cac:DeliveryLocation/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:DeliveryParty/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:DeliveryParty/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/BT-71 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_BT-71</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:Delivery/cac:DeliveryLocation | cn:CreditNote/cac:CreditNoteLine/cac:Delivery/cac:DeliveryLocation"
                 priority="1000"
                 mode="M27">
      <xsl:variable name="siret" select="cac:DeliveryLocation/cbc:ID[@schemeID='0009']"/>
      <xsl:variable name="siren"
                    select="if (string(cac:DeliveryParty/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'])) then cac:DeliveryParty/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002'] else substring($siret[1], 1, 9)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($siret) or custom:check-siret-siren-coherence($siret[1], $siren)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-09/EXT-FR-FE-146 : Le SIRET doit contenir 14 chiffres et commencer par le SIREN. SIRET : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siret"/>
               <xsl:text/>
               <xsl:text>", SIREN : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-09_EXT-FR-FE-146</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M27"/>
   <xsl:template match="@*|node()" priority="-2" mode="M27">
      <xsl:apply-templates select="@*|*" mode="M27"/>
   </xsl:template>
   <!--PATTERN BR-FR-10BR-FR-10 — SIREN du vendeur obligatoire et valide (BT-30)-->
   <!--RULE -->
   <xsl:template match="cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity"
                 priority="1000"
                 mode="M28">
      <xsl:variable name="siren" select="cbc:CompanyID[@schemeID='0002']"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="$siren and matches(normalize-space($siren), '^\d{9}$')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-10/BT-30 : Le SIREN du vendeur (CompanyID[@schemeID='0002']) est obligatoire et doit être composé exactement de 9 chiffres. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". Veuillez renseigner un identifiant SIREN valide. </xsl:text>
               <xsl:text>
ID:BR-FR-10_BT-30</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M28"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M28"/>
   <xsl:template match="@*|node()" priority="-2" mode="M28">
      <xsl:apply-templates select="@*|*" mode="M28"/>
   </xsl:template>
   <!--PATTERN BR-FR-11BR-FR-11 — SIREN obligatoire et valide si traitement BAR/B2B (BT-47)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M29">
      <xsl:variable name="allNotes"
                    select="string-join(./cbc:Note, '')[contains(., '#BAR#')]"/>
      <xsl:variable name="afterBar" select="substring-after($allNotes, '#BAR#')"/>
      <xsl:variable name="barTreatment"
                    select="if (contains($afterBar, '#')) then substring-before($afterBar, '#') else $afterBar"/>
      <xsl:variable name="siren"
                    select="cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002']"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($barTreatment='B2B') or ($siren and matches(normalize-space($siren), '^\d{9}$'))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-11/BT-47 : Si une note contient le code sujet BAR avec la valeur 'B2B', alors le SIREN de l’acheteur (cbc:ID[@schemeID='0002']) est obligatoire et doit être composé exactement de 9 chiffres. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". Veuillez renseigner un identifiant SIREN valide. </xsl:text>
               <xsl:text>
ID:BR-FR-11_BT-47</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M29"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M29"/>
   <xsl:template match="@*|node()" priority="-2" mode="M29">
      <xsl:apply-templates select="@*|*" mode="M29"/>
   </xsl:template>
   <!--PATTERN BR-FR-12BR-FR-12 — Vérification de la présence du BT-49-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M30">
      <xsl:variable name="endpointID"
                    select="cac:AccountingCustomerParty/cac:Party/cbc:EndpointID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space($endpointID) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-12/BT-49 : Le BT-49 (cbc:EndpointID) est obligatoire. Valeur actuelle : BT-49="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$endpointID"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-12_BT-49</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M30"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M30"/>
   <xsl:template match="@*|node()" priority="-2" mode="M30">
      <xsl:apply-templates select="@*|*" mode="M30"/>
   </xsl:template>
   <!--PATTERN BR-FR-13BR-FR-13 — Vérification de la présence du BT-34-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M31">
      <xsl:variable name="endpointID"
                    select="cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space($endpointID) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-13/BT-34 : Le BT-34 (cbc:EndpointID du vendeur) est obligatoire. Valeur actuelle : BT-34="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$endpointID"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-13_BT-34</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M31"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M31"/>
   <xsl:template match="@*|node()" priority="-2" mode="M31">
      <xsl:apply-templates select="@*|*" mode="M31"/>
   </xsl:template>
   <!--PATTERN BR-FR-15BR-FR-15 — Vérification des codes de catégorie de TVA (BT-95, BT-102, BT-118, BT-151)-->
   <!--RULE -->
   <xsl:template match="cac:AllowanceCharge/cac:TaxCategory"
                 priority="1002"
                 mode="M32">
      <xsl:variable name="categoryCode" select="cbc:ID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode) or custom:is-valid-vat-category-code($categoryCode)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-95/BT-102 : Code de catégorie de TVA invalide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code valide : S, E, AE, K, G, O, Z. </xsl:text>
               <xsl:text>
ID:BR-FR-15_BT-95_BT-102-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode = ('L', 'M'))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-95/BT-102 : Les codes 'L' et 'M' ne sont pas pertinents en France. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-15_BT-95_BT-102-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M32"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory"
                 priority="1001"
                 mode="M32">
      <xsl:variable name="categoryCode" select="cbc:ID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode) or custom:is-valid-vat-category-code($categoryCode)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-118 : Code de catégorie de TVA invalide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code valide : S, E, AE, K, G, O, Z. </xsl:text>
               <xsl:text>
ID:BR-FR-15_BT-118-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode = ('L', 'M'))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-118 : Les codes 'L' et 'M' ne sont pas pertinents en France. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-15_BT-118-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M32"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:Item/cac:ClassifiedTaxCategory"
                 priority="1000"
                 mode="M32">
      <xsl:variable name="categoryCode" select="cbc:ID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode) or custom:is-valid-vat-category-code($categoryCode)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-151 : Code de catégorie de TVA invalide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". Veuillez utiliser un code valide : S, E, AE, K, G, O, Z. </xsl:text>
               <xsl:text>
ID:BR-FR-15_BT-151-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($categoryCode = ('L', 'M'))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-15/BT-151 : Les codes 'L' et 'M' ne sont pas pertinents en France. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$categoryCode"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-08_BT-151-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M32"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M32"/>
   <xsl:template match="@*|node()" priority="-2" mode="M32">
      <xsl:apply-templates select="@*|*" mode="M32"/>
   </xsl:template>
   <!--PATTERN BR-FR-16BR-FR-16 — Vérification des taux de TVA autorisés (BT-96, BT-103, BT-119, BT-152)-->
   <!--RULE -->
   <xsl:template match="cac:AllowanceCharge/cac:TaxCategory"
                 priority="1003"
                 mode="M33">
      <xsl:variable name="vatRate" select="cbc:Percent"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($vatRate) or custom:is-valid-vat-rate($vatRate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-16/BT-96 : Le taux de TVA (cbc:Percent) doit être exprimé en pourcentage sans symbole « % » et faire partie des valeurs autorisées. Taux fourni : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$vatRate"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-16_BT-96</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M33"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AllowanceCharge/cac:TaxCategory"
                 priority="1002"
                 mode="M33">
      <xsl:variable name="vatRate" select="cbc:Percent"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($vatRate) or custom:is-valid-vat-rate($vatRate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-16/BT-103 : Le taux de TVA (cbc:Percent) doit être exprimé en pourcentage sans symbole « % » et faire partie des valeurs autorisées. Taux fourni : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$vatRate"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-16_BT-103</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M33"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory"
                 priority="1001"
                 mode="M33">
      <xsl:variable name="vatRate" select="cbc:Percent"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($vatRate) or custom:is-valid-vat-rate($vatRate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-16/BT-119 : Le taux de TVA (cbc:Percent) doit être exprimé en pourcentage sans symbole « % » et faire partie des valeurs autorisées. Taux fourni : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$vatRate"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-16_BT-119</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M33"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:InvoiceLine/cac:Item/cac:ClassifiedTaxCategory"
                 priority="1000"
                 mode="M33">
      <xsl:variable name="vatRate" select="cbc:Percent"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($vatRate) or custom:is-valid-vat-rate($vatRate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-16/BT-152 : Le taux de TVA (cbc:Percent) doit être exprimé en pourcentage sans symbole « % » et faire partie des valeurs autorisées. Taux fourni : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$vatRate"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-16_BT-152</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M33"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M33"/>
   <xsl:template match="@*|node()" priority="-2" mode="M33">
      <xsl:apply-templates select="@*|*" mode="M33"/>
   </xsl:template>
   <!--PATTERN BR-FR-17BR-FR-17 — Codes autorisés pour qualifier les pièces jointes (BT-123)-->
   <!--RULE -->
   <xsl:template match="cac:AdditionalDocumentReference" priority="1000" mode="M34">
      <xsl:variable name="docTypeDESC" select="cbc:DocumentDescription"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($docTypeDESC) or custom:is-valid-attachment-code($docTypeDESC)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-17/BT-123 : Le code de qualification de la pièce jointe "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$docTypeDESC"/>
               <xsl:text/>
               <xsl:text>" est invalide. Il doit appartenir à la liste des codes autorisés. Veuillez corriger la valeur de BT-123. </xsl:text>
               <xsl:text>
ID:BR-FR-17_BT-123</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M34"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M34"/>
   <xsl:template match="@*|node()" priority="-2" mode="M34">
      <xsl:apply-templates select="@*|*" mode="M34"/>
   </xsl:template>
   <!--PATTERN BR-FR-18BR-FR-18 — Un seul document additionnel avec la description "LISIBLE" (BT-123)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M35">
      <xsl:variable name="lisibleCount"
                    select="count(cac:AdditionalDocumentReference[cbc:DocumentDescription = 'LISIBLE'])"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="$lisibleCount le 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-18/BT-123 : Il ne peut y avoir </xsl:text>
               <xsl:text/>
               <xsl:value-of select="'qu’un seul'"/>
               <xsl:text/>
               <xsl:text> document additionnel (cac:AdditionalDocumentReference) dont la description (cbc:DocumentDescription) est "LISIBLE". Nombre de documents trouvés : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$lisibleCount"/>
               <xsl:text/>
               <xsl:text>. Veuillez supprimer les doublons ou corriger les descriptions. </xsl:text>
               <xsl:text>
ID:BR-FR-18_BT-123</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M35"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M35"/>
   <xsl:template match="@*|node()" priority="-2" mode="M35">
      <xsl:apply-templates select="@*|*" mode="M35"/>
   </xsl:template>
   <!--PATTERN BR-FR-20BR-FR-20 — Vérification du traitement associé à une note avec code sujet "BAR" (BT-21)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M36">
      <xsl:variable name="allNotes"
                    select="string-join(./cbc:Note, '')[contains(., '#BAR#')]"/>
      <xsl:variable name="afterBar" select="substring-after($allNotes, '#BAR#')"/>
      <xsl:variable name="barTreatment"
                    select="if (contains($afterBar, '#')) then substring-before($afterBar, '#') else $afterBar"/>
      <xsl:variable name="invalidNotes"
                    select="$barTreatment != '' and $barTreatment != 'B2B' and $barTreatment != 'B2BINT' and $barTreatment != 'B2C' and $barTreatment != 'OUTOFSCOPE' and $barTreatment != 'ARCHIVEONLY'"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($invalidNotes)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-20/BT-21 : Lorsqu’une note a pour code sujet « BAR » (cbc:SubjectCode), la valeur associée (cbc:Note) doit être l’une des suivantes : B2B, B2BINT, B2C, OUTOFSCOPE, ARCHIVEONLY. Valeur fournie : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$barTreatment"/>
               <xsl:text/>
               <xsl:text>". Veuillez corriger la valeur ou retirer le code sujet « BAR ». </xsl:text>
               <xsl:text>
ID:BR-FR-20_BT-21</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M36"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M36"/>
   <xsl:template match="@*|node()" priority="-2" mode="M36">
      <xsl:apply-templates select="@*|*" mode="M36"/>
   </xsl:template>
   <!--PATTERN BR-FR-21BR-FR-21 — Vérification du BT-49 en cas de traitement BAR/B2B et hors cas autofacture-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M37">
      <xsl:variable name="allNotes"
                    select="string-join(./cbc:Note, '')[contains(., '#BAR#')]"/>
      <xsl:variable name="afterBar" select="substring-after($allNotes, '#BAR#')"/>
      <xsl:variable name="treatment"
                    select="if (contains($afterBar, '#')) then substring-before($afterBar, '#') else $afterBar"/>
      <xsl:variable name="typeCode" select="cbc:InvoiceTypeCode | cbc:CreditNoteTypeCode"/>
      <xsl:variable name="siren"
                    select="cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002']"/>
      <xsl:variable name="endpointID"
                    select="cac:AccountingCustomerParty/cac:Party/cbc:EndpointID"/>
      <xsl:variable name="schemeID"
                    select="cac:AccountingCustomerParty/cac:Party/cbc:EndpointID/@schemeID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($treatment='B2B') or $typeCode = ('389', '501', '500', '471', '473', '261', '502') or (starts-with($endpointID, $siren) and $schemeID = '0225')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-21/BT-49 : Si le traitement est BAR/B2B et que le type de document (cbc:InvoiceTypeCode) n’est pas en autofacture (389, 501, 500, 471, 473, 261, 502), alors le BT-49 (cbc:EndpointID) doit commencer par le SIREN (cbc:ID[@schemeID='0002']) et le schemeID doit être égal à "0225". Valeurs actuelles : BAR = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$treatment"/>
               <xsl:text/>
               <xsl:text>", EndpointID="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$endpointID"/>
               <xsl:text/>
               <xsl:text>", schemeID="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$schemeID"/>
               <xsl:text/>
               <xsl:text>", SIREN="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-21_BT-49</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M37"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M37"/>
   <xsl:template match="@*|node()" priority="-2" mode="M37">
      <xsl:apply-templates select="@*|*" mode="M37"/>
   </xsl:template>
   <!--PATTERN BR-FR-22BR-FR-22 — Vérification du BT-34 en cas de traitement BAR/B2B et en autofacture-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M38">
      <xsl:variable name="allNotes"
                    select="string-join(./cbc:Note, '')[contains(., '#BAR#')]"/>
      <xsl:variable name="afterBar" select="substring-after($allNotes, '#BAR#')"/>
      <xsl:variable name="treatment"
                    select="if (contains($afterBar, '#')) then substring-before($afterBar, '#') else $afterBar"/>
      <xsl:variable name="typeCode" select="cbc:InvoiceTypeCode | cbc:CreditNoteTypeCode"/>
      <xsl:variable name="siren"
                    select="cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID[@schemeID='0002']"/>
      <xsl:variable name="endpointID"
                    select="cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"/>
      <xsl:variable name="schemeID"
                    select="cac:AccountingSupplierParty/cac:Party/cbc:EndpointID/@schemeID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($treatment) or not($typeCode = ('389', '501', '500', '471', '473', '261', '502')) or          (starts-with($endpointID, $siren) and $schemeID = '0225')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-22/BT-34 : Si le traitement est BAR/B2B et que le type de document (cbc:InvoiceTypeCode) est en autofacture (389, 501, 500, 471, 473, 261, 502), alors le BT-34 (cbc:EndpointID du vendeur) doit commencer par le SIREN (cbc:ID[@schemeID='0002']) et le schemeID doit être égal à "0225". Valeurs actuelles : EndpointID="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$endpointID"/>
               <xsl:text/>
               <xsl:text>", schemeID="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$schemeID"/>
               <xsl:text/>
               <xsl:text>", SIREN="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$siren"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-22_BT-34</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M38"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M38"/>
   <xsl:template match="@*|node()" priority="-2" mode="M38">
      <xsl:apply-templates select="@*|*" mode="M38"/>
   </xsl:template>
   <!--PATTERN BR-FR-23BR-FR-23 — Validation du format des adresses électroniques avec schemeID = 0225-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cbc:EndpointID[@schemeID='0225']"
                 priority="1007"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/BT-34 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_BT-34</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cbc:EndpointID[@schemeID='0225']"
                 priority="1006"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/BT-49 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_BT-49</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:AgentParty/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:AgentParty/cbc:EndpointID[@schemeID='0225']"
                 priority="1005"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-12 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-12</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PayeeParty/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:PayeeParty/cbc:EndpointID[@schemeID='0225']"
                 priority="1004"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-29 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-29</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty/cbc:EndpointID[@schemeID='0225']"
                 priority="1003"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-52 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-52</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:AgentParty/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:AgentParty/cbc:EndpointID[@schemeID='0225']"
                 priority="1002"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-75 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-75</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID[@schemeID='0225']"
                 priority="1001"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-98 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-98</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID[@schemeID='0225'] | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID[@schemeID='0225']"
                 priority="1000"
                 mode="M39">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-23/EXT-FR-FE-121 : L'adresse électronique (cbc:EndpointID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-23_EXT-FR-FE-121</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M39"/>
   <xsl:template match="@*|node()" priority="-2" mode="M39">
      <xsl:apply-templates select="@*|*" mode="M39"/>
   </xsl:template>
   <!--PATTERN BR-FR-24BR-FR-24 — Validation du format des identifiants privés avec schemeID = 0224-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224'] | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224']"
                 priority="1001"
                 mode="M40">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-24/BT-29 : L'identifiant privé (cbc:ID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-24_BT-29</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M40"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224'] | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224']"
                 priority="1000"
                 mode="M40">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-schemeid-format(.)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-24/BT-46 : L'identifiant privé (cbc:ID) ne respecte pas le format autorisé. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Seuls les caractères alphanumériques et les symboles "-", "_", "." sont autorisés. </xsl:text>
               <xsl:text>
ID:BR-FR-24_BT-46</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M40"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M40"/>
   <xsl:template match="@*|node()" priority="-2" mode="M40">
      <xsl:apply-templates select="@*|*" mode="M40"/>
   </xsl:template>
   <!--PATTERN BR-FR-25BR-FR-25 — Longueur maximale des adresses électroniques-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cbc:EndpointID | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"
                 priority="1007"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/BT-34 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_BT-34</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cbc:EndpointID | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cbc:EndpointID"
                 priority="1006"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/BT-49 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_BT-49</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:AgentParty/cbc:EndpointID | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:AgentParty/cbc:EndpointID"
                 priority="1005"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-12 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-12</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PayeeParty/cbc:EndpointID | cn:CreditNote/cac:PayeeParty/cbc:EndpointID"
                 priority="1004"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-29 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-29</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty/cbc:EndpointID | cn:CreditNote/cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty/cbc:EndpointID"
                 priority="1003"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-52 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-52</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:AgentParty/cbc:EndpointID | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:AgentParty/cbc:EndpointID"
                 priority="1002"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-75 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-75</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID"
                 priority="1001"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-98 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-98</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party/cbc:EndpointID"
                 priority="1000"
                 mode="M41">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 125"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-25/EXT-FR-FE-121 : L'adresse électronique (cbc:EndpointID) dépasse 125 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-25_EXT-FR-FE-121</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M41"/>
   <xsl:template match="@*|node()" priority="-2" mode="M41">
      <xsl:apply-templates select="@*|*" mode="M41"/>
   </xsl:template>
   <!--PATTERN BR-FR-26BR-FR-26 — Longueur maximale des identifiants privés avec schemeID = 0224-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224'] | cn:CreditNote/cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224']"
                 priority="1001"
                 mode="M42">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 100"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-26/BT-29 : L'identifiant privé (cbc:ID) dépasse 100 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-26_BT-29</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M42"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224'] | cn:CreditNote/cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='0224']"
                 priority="1000"
                 mode="M42">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="string-length(.) le 100"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-26/BT-46 : L'identifiant privé (cbc:ID) dépasse 100 caractères. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez raccourcir cette valeur pour respecter la limite. </xsl:text>
               <xsl:text>
ID:BR-FR-26_BT-46</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M42"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M42"/>
   <xsl:template match="@*|node()" priority="-2" mode="M42">
      <xsl:apply-templates select="@*|*" mode="M42"/>
   </xsl:template>
   <!--PATTERN BR-FR-27BR-FR-27 — Validation du groupe Attribut d’article (BG-32)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty | cn:CreditNote/cac:Item/cac:AdditionalItemProperty"
                 priority="1002"
                 mode="M43">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="cbc:Name or cbc:NameCode"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-27/BG-32 : Le groupe Attribut d’article (BG-32) doit contenir soit un nom d’attribut d’article (BT-160 : cbc:Name), soit un code d’attribut d’article (EXT-FR-FE-159 : cbc:NameCode). Aucun des deux éléments n’a été trouvé dans le contexte /cac:Item/cac:AdditionalItemProperty. Veuillez ajouter au moins l’un des deux éléments pour respecter la structure attendue. </xsl:text>
               <xsl:text>
ID:BR-FR-27_BG-32</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M43"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty/cbc:Name | cn:CreditNote/cac:Item/cac:AdditionalItemProperty/cbc:Name"
                 priority="1001"
                 mode="M43">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-27/BT-160 : Le nom d’attribut d’article (cbc:Name) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez fournir un nom d’attribut valide ou utiliser un code à la place. </xsl:text>
               <xsl:text>
ID:BR-FR-27_BT-160</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M43"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty/cbc:NameCode | cn:CreditNote/cac:Item/cac:AdditionalItemProperty/cbc:NameCode"
                 priority="1000"
                 mode="M43">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-27/EXT-FR-FE-159 : Le code d’attribut d’article (cbc:NameCode) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez fournir un code d’attribut valide ou utiliser un nom à la place. </xsl:text>
               <xsl:text>
ID:BR-FR-27_EXT-FR-FE-159</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M43"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M43"/>
   <xsl:template match="@*|node()" priority="-2" mode="M43">
      <xsl:apply-templates select="@*|*" mode="M43"/>
   </xsl:template>
   <!--PATTERN BR-FR-28BR-FR-28 — Validation de la valeur d’attribut d’article (BG-32)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty | cn:CreditNote/cac:Item/cac:AdditionalItemProperty"
                 priority="1003"
                 mode="M44">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="(cbc:Value or (cbc:ValueQuantity and cbc:ValueQuantity/@unitCode)) and not(cbc:Value or (cbc:ValueQuantity and cbc:ValueQuantity/@unitCode))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-28/BT-161 : Le groupe Attribut d’article (BG-32) doit contenir soit une valeur d’attribut (BT-161 : cbc:Value), soit une valeur d’attribut avec unité de mesure (EXT-FR-FE-160 : cbc:ValueQuantity) accompagnée de son unité (EXT-FR-FE-161 : @unitCode), et pas les deux. Veuillez fournir une valeur d’attribut ou une valeur mesurée avec son unité et pas les deux. </xsl:text>
               <xsl:text>
ID:BR-FR-28_BT-161</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M44"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty/cbc:Value | cn:CreditNote/cac:Item/cac:AdditionalItemProperty/cbc:Value"
                 priority="1002"
                 mode="M44">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-28/BT-161 : La valeur d’attribut (cbc:Value) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez fournir une valeur d’attribut valide ou utiliser une mesure avec unité. </xsl:text>
               <xsl:text>
ID:BR-FR-28_Value</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M44"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty/cbc:ValueQuantity | cn:CreditNote/cac:Item/cac:AdditionalItemProperty/cbc:ValueQuantity"
                 priority="1001"
                 mode="M44">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-28/EXT-FR-FE-160 : La valeur mesurée (cbc:ValueQuantity) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez fournir une valeur mesurée valide accompagnée de son unité. </xsl:text>
               <xsl:text>
ID:BR-FR-28_ValueQuantity</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M44"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Item/cac:AdditionalItemProperty/cbc:ValueQuantity/@unitCode | cn:CreditNote/cac:Item/cac:AdditionalItemProperty/cbc:ValueQuantity/@unitCode"
                 priority="1000"
                 mode="M44">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-28/EXT-FR-FE-161 : L’unité de mesure (@unitCode) ne doit pas être vide lorsqu’une valeur mesurée est fournie. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". Veuillez spécifier une unité de mesure conforme. </xsl:text>
               <xsl:text>
ID:BR-FR-28_UnitCode</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M44"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M44"/>
   <xsl:template match="@*|node()" priority="-2" mode="M44">
      <xsl:apply-templates select="@*|*" mode="M44"/>
   </xsl:template>
   <!--PATTERN BR-FR-29BR-FR-29 — Vérification des identifiants d’objets facturés (BT-18)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AdditionalDocumentReference | cn:CreditNote/cac:AdditionalDocumentReference"
                 priority="1002"
                 mode="M45">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(cbc:ID[@schemeID='AFL']) &lt;= 1 and count(cbc:ID[@schemeID='AVV']) &lt;= 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-29/BT-18 : Parmi les identifiants d’objets facturés (BT-18), les schémas d’identification "AFL" et "AVV" ne doivent être présents qu’une seule fois chacun. Actuellement : AFL = </xsl:text>
               <xsl:text/>
               <xsl:value-of select="count(cbc:ID[@schemeID='AFL'])"/>
               <xsl:text/>
               <xsl:text> occurrence(s), AVV = </xsl:text>
               <xsl:text/>
               <xsl:value-of select="count(cbc:ID[@schemeID='AVV'])"/>
               <xsl:text/>
               <xsl:text> occurrence(s). Veuillez supprimer les doublons pour respecter la règle. </xsl:text>
               <xsl:text>
ID:BR-FR-29_BT-18</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M45"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AdditionalDocumentReference/cbc:ID[@schemeID='AFL'] | cn:CreditNote/cac:AdditionalDocumentReference/cbc:ID[@schemeID='AFL']"
                 priority="1001"
                 mode="M45">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-29/AFL : L’identifiant associé au schéma "AFL" (cbc:ID) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-29_AFL</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M45"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AdditionalDocumentReference/cbc:ID[@schemeID='AVV'] | cn:CreditNote/cac:AdditionalDocumentReference/cbc:ID[@schemeID='AVV']"
                 priority="1000"
                 mode="M45">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-29/AVV : L’identifiant associé au schéma "AVV" (cbc:ID) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-29_AVV</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M45"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M45"/>
   <xsl:template match="@*|node()" priority="-2" mode="M45">
      <xsl:apply-templates select="@*|*" mode="M45"/>
   </xsl:template>
   <!--PATTERN BR-FR-30BR-FR-30 — Vérification des identifiants d’objets facturés à la ligne (BT-128)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:DocumentReference | cn:CreditNote/cac:CreditNoteLine/cac:DocumentReference"
                 priority="1002"
                 mode="M46">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(cbc:ID[@schemeID='AFL']) &lt;= 1 and count(cbc:ID[@schemeID='AVV']) &lt;= 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-30/BT-128 : Parmi les identifiants d’objets facturés à la ligne (BT-128), les schémas d’identification "AFL" et "AVV" ne doivent être présents qu’une seule fois chacun. Actuellement : AFL = </xsl:text>
               <xsl:text/>
               <xsl:value-of select="count(cbc:ID[@schemeID='AFL'])"/>
               <xsl:text/>
               <xsl:text> occurrence(s), AVV = </xsl:text>
               <xsl:text/>
               <xsl:value-of select="count(cbc:ID[@schemeID='AVV'])"/>
               <xsl:text/>
               <xsl:text> occurrence(s). Veuillez supprimer les doublons pour respecter la règle. </xsl:text>
               <xsl:text>
ID:BR-FR-30_BT-128</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M46"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:DocumentReference/cbc:ID[@schemeID='AFL'] | cn:CreditNote/cac:CreditNoteLine/cac:DocumentReference/cbc:ID[@schemeID='AFL']"
                 priority="1001"
                 mode="M46">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-30/AFL : L’identifiant associé au schéma "AFL" (cbc:ID) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-30_AFL</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M46"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:DocumentReference/cbc:ID[@schemeID='AVV'] | cn:CreditNote/cac:CreditNoteLine/cac:DocumentReference/cbc:ID[@schemeID='AVV']"
                 priority="1000"
                 mode="M46">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="normalize-space(.) != ''"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-30/AVV : L’identifiant associé au schéma "AVV" (cbc:ID) ne doit pas être vide. Valeur actuelle : "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-30_AVV</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M46"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M46"/>
   <xsl:template match="@*|node()" priority="-2" mode="M46">
      <xsl:apply-templates select="@*|*" mode="M46"/>
   </xsl:template>
   <!--PATTERN BR-FR-31BR-FR-31 — Note avec code sujet BAR : une seule valeur possible dans la liste-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M47">
      <xsl:variable name="allBarNotes"
                    select="concat(string-join(./cbc:Note[contains(., '#BAR#')], ''), '#')"/>
      <xsl:variable name="countBarB2B"
                    select="(string-length($allBarNotes) - string-length(replace($allBarNotes, 'BAR#B2B#', ''))) div 8"/>
      <xsl:variable name="countBarB2BINT"
                    select="(string-length($allBarNotes) - string-length(replace($allBarNotes, 'BAR#B2BINT#', ''))) div 11"/>
      <xsl:variable name="countBarB2C"
                    select="(string-length($allBarNotes) - string-length(replace($allBarNotes, 'BAR#B2C#', ''))) div 8"/>
      <xsl:variable name="countBarOUTOFSCOPE"
                    select="(string-length($allBarNotes) - string-length(replace($allBarNotes, 'BAR#OUTOFSCOPE#', ''))) div 15"/>
      <xsl:variable name="countBarARCHIVEONLY"
                    select="(string-length($allBarNotes) - string-length(replace($allBarNotes, 'BAR#ARCHIVEONLY#', ''))) div 16"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="($countBarB2B + $countBarB2BINT + $countBarB2C + $countBarOUTOFSCOPE + $countBarARCHIVEONLY) &lt;= 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-30/BT-21 : Lorsque plusieurs notes ont le code sujet « BAR » (BT-21), Il ne peut y avoir qu'une seule valeur associée (BT-22, contenu de la note) parmi l’une des suivantes : B2B, B2BINT, B2C, OUTOFSCOPE, ARCHIVEONLY. Valeur fournie : B2B : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$countBarB2B"/>
               <xsl:text/>
               <xsl:text> , B2BINT : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$countBarB2BINT"/>
               <xsl:text/>
               <xsl:text>, B2C : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$countBarB2C"/>
               <xsl:text/>
               <xsl:text>, OUTOFSCOPE : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$countBarOUTOFSCOPE"/>
               <xsl:text/>
               <xsl:text>, ARCHIVEONLY : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$countBarARCHIVEONLY"/>
               <xsl:text/>
               <xsl:text>". Veuillez corriger la valeur ou retirer le code sujet « BAR ». </xsl:text>
               <xsl:text>
ID:BR-FR-30_BT-21</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M47"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M47"/>
   <xsl:template match="@*|node()" priority="-2" mode="M47">
      <xsl:apply-templates select="@*|*" mode="M47"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-03BR-FR-CO-03 — Présence obligatoire du contrat et de la période de facturation si type de facture = 262 (Avoir Remise Globale)-->
   <!--RULE -->
   <xsl:template match="cn:CreditNote" priority="1000" mode="M48">
      <xsl:variable name="typeCode" select="cbc:CreditNoteTypeCode"/>
      <xsl:variable name="contractReference" select="cac:ContractDocumentReference/cbc:ID"/>
      <xsl:variable name="billingPeriodStart" select="cac:InvoicePeriod/cbc:StartDate"/>
      <xsl:variable name="billingPeriodEnd" select="cac:InvoicePeriod/cbc:EndDate"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($typeCode = '262') or (string($contractReference) and string($billingPeriodStart) and string($billingPeriodEnd))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-03/BT-3 : Si le code type de la facture (BT-3) est égal à 262 (Avoir Remise Globale), alors : - Le numéro de contrat (BT-12) doit être présent - La période de facturation (BG-14) doit être renseignée (dates de début et de fin). Valeurs actuelles : BT-12="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$contractReference"/>
               <xsl:text/>
               <xsl:text>", période="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$billingPeriodStart"/>
               <xsl:text/>
               <xsl:text> à </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$billingPeriodEnd"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-CO-03_BT-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M48"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M48"/>
   <xsl:template match="@*|node()" priority="-2" mode="M48">
      <xsl:apply-templates select="@*|*" mode="M48"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-04BR-FR-CO-04 — Une seule référence à une facture antérieure obligatoire pour les factures rectificatives (BT-3)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M49">
      <xsl:variable name="typeCode" select="cbc:InvoiceTypeCode"/>
      <xsl:variable name="references" select="cac:BillingReference"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($typeCode = '384' or $typeCode = '471' or $typeCode = '472' or $typeCode = '473') or count($references) = 1"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-04/BT-3 : Si le type de facture (BT-3) est une facture rectificative (384, 471, 472, 473), alors **une et une seule** référence à une facture antérieure (BT-25) avec sa date (BT-26) doit être présente. Nombre de références valides trouvées : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="count($references)"/>
               <xsl:text/>
               <xsl:text>. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-04_BT-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M49"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M49"/>
   <xsl:template match="@*|node()" priority="-2" mode="M49">
      <xsl:apply-templates select="@*|*" mode="M49"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-05BR-FR-CO-05 — Référence obligatoire à une facture antérieure pour les avoirs (BT-3)-->
   <!--RULE -->
   <xsl:template match="cn:CreditNote" priority="1000" mode="M50">
      <xsl:variable name="typeCode" select="cbc:CreditNoteTypeCode"/>
      <xsl:variable name="headerReferences"
                    select="cac:BillingReference/cac:InvoiceDocumentReference"/>
      <xsl:variable name="headerRefCount"
                    select="count($headerReferences[cbc:ID and cbc:IssueDate])"/>
      <xsl:variable name="lineReferences"
                    select="cac:CreditNoteLine/cac:BillingReference/cac:InvoiceDocumentReference[cbc:ID and cbc:IssueDate]"/>
      <xsl:variable name="lineCount" select="count(cac:CreditNoteLine)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($typeCode = '261' or $typeCode = '381' or $typeCode = '396' or $typeCode = '502' or $typeCode = '503') or ($headerRefCount &gt; 0 or count($lineReferences) = $lineCount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-05/BT-3 : Si le type de facture (BT-3) est un avoir (261, 381, 396, 502, 503), alors : - soit au moins une référence à une facture antérieure (BT-25) avec sa date (BT-26) doit être présente au niveau entête, - soit chaque ligne (BG-25) doit contenir une référence à une facture antérieure (EXT-FR-FE-136) avec sa date (EXT-FR-FE-138). Références entête trouvées : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$headerRefCount"/>
               <xsl:text/>
               <xsl:text>. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-05_BT-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M50"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M50"/>
   <xsl:template match="@*|node()" priority="-2" mode="M50">
      <xsl:apply-templates select="@*|*" mode="M50"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-07BR-FR-CO-07 — La date d’échéance (BT-9) doit être postérieure ou égale à la date de facture (BT-2), sauf cas particuliers-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M51">
      <xsl:variable name="typeCode" select="cbc:InvoiceTypeCode | cbc:CreditNoteTypeCode"/>
      <xsl:variable name="billingContext" select="cac:PaymentTerms/cbc:Note"/>
      <xsl:variable name="issueDate" select="cbc:IssueDate"/>
      <xsl:variable name="dueDate" select="cbc:DueDate"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($dueDate and not($typeCode = '386' or $typeCode = '500' or $typeCode = '503' or $billingContext = 'B2' or $billingContext = 'S2' or $billingContext = 'M2') and $dueDate &lt; $issueDate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-07/BT-9 : La date d’échéance (BT-9), si présente, doit être postérieure ou égale à la date de facture (BT-2), sauf si la facture est de type acompte (386, 500, 503) ou si le cadre de facturation (BT-23) est B2, S2 ou M2. Valeurs actuelles : Date facture = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$issueDate"/>
               <xsl:text/>
               <xsl:text>", Date échéance = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$dueDate"/>
               <xsl:text/>
               <xsl:text>", Type = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$typeCode"/>
               <xsl:text/>
               <xsl:text>", Cadre = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$billingContext"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-CO-07_BT-9</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M51"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M51"/>
   <xsl:template match="@*|node()" priority="-2" mode="M51">
      <xsl:apply-templates select="@*|*" mode="M51"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-08BR-FR-CO-08 — Incompatibilité entre cadre de facturation (BT-23) et type de facture (BT-3)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M52">
      <xsl:variable name="typeCode" select="cbc:InvoiceTypeCode | cbc:CreditNoteTypeCode"/>
      <xsl:variable name="billingContext" select="cac:PaymentTerms/cbc:Note"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($billingContext = 'B4' or $billingContext = 'S4' or $billingContext = 'M4') or not($typeCode = '386' or $typeCode = '500' or $typeCode = '503')"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-08/BT-23 : Si le cadre de facturation (BT-23) est B4, S4 ou M4 (factures définitives après acompte), alors le type de facture (BT-3) ne peut pas être une facture ou un avoir d’acompte (386, 500, 503). Valeurs actuelles : BT-23="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$billingContext"/>
               <xsl:text/>
               <xsl:text>", BT-3="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$typeCode"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-CO-08_BT-23</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M52"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M52"/>
   <xsl:template match="@*|node()" priority="-2" mode="M52">
      <xsl:apply-templates select="@*|*" mode="M52"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-09BR-FR-CO-09 — Contrôle des montants et de la date d’échéance pour les factures déjà payées (BT-23)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M53">
      <xsl:variable name="billingContext" select="cac:PaymentTerms/cbc:Note"/>
      <xsl:variable name="paidAmount" select="cac:LegalMonetaryTotal/cbc:PrepaidAmount"/>
      <xsl:variable name="grandTotal"
                    select="cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"/>
      <xsl:variable name="payableAmount" select="cac:LegalMonetaryTotal/cbc:PayableAmount"/>
      <xsl:variable name="dueDate" select="cbc:DueDate"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($billingContext = 'B2' or $billingContext = 'S2' or $billingContext = 'M2') or (number($paidAmount) = number($grandTotal))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-09/BT-23 : Si le cadre de facturation (BT-23) est B2, S2 ou M2 (facture déjà payée), alors le montant déjà payé (BT-113) doit être égal au montant total TTC (BT-112). Montant payé : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$paidAmount"/>
               <xsl:text/>
               <xsl:text>, Montant total : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$grandTotal"/>
               <xsl:text/>
               <xsl:text>. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-09_BT-23-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($billingContext = 'B2' or $billingContext = 'S2' or $billingContext = 'M2') or (number($payableAmount) = 0)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-09/BT-23 : Si le cadre de facturation (BT-23) est B2, S2 ou M2, alors le net à payer (BT-115) doit être égal à 0. Net à payer : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$payableAmount"/>
               <xsl:text/>
               <xsl:text>. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-09_BT-23-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($billingContext = 'B2' or $billingContext = 'S2' or $billingContext = 'M2') or string($dueDate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-09/BT-23 : Si le cadre de facturation (BT-23) est B2, S2 ou M2, alors la date d’échéance (BT-9) doit être renseignée et correspondre à la date de paiement. Date d’échéance actuelle : </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$dueDate"/>
               <xsl:text/>
               <xsl:text>. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-09_BT-23-3</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M53"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M53"/>
   <xsl:template match="@*|node()" priority="-2" mode="M53">
      <xsl:apply-templates select="@*|*" mode="M53"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-10BR-FR-CO-10 — Vérification de la présence du schéma d’identifiant global (BT-29 et équivalents)-->
   <!--RULE -->
   <xsl:template match="cac:AccountingSupplierParty/cac:Party"
                 priority="1009"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-29 : Chaque identifiant global du vendeur (BT-29) doit avoir un attribut schemeID (BT-29-1). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-29-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-29 : Chaque schemeID ne peut apparaître qu’une seule fois dans l'identifiant privé du vendeur (BT-29). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-29-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AccountingCustomerParty/cac:Party"
                 priority="1008"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-46 : Si l’identifiant global de l'acheteur (BT-46) est renseigné, alors son schéma (BT-46-1) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-46-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-46 : Chaque schemeID ne peut apparaître qu’une seule fois dans l'identifiant privé de l'acheteur (BT-46). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-46-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:PayeeParty" priority="1007" mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-60 : Si l’identifiant global du bénéficiaire (BT-60) est renseigné, alors son schéma (BT-60-1) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-60-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-60 : Chaque schemeID ne peut apparaître qu’une seule fois dans l'identifiant privé du bénéficiaire (BT-60). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-60-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AccountingCustomerParty/cac:Party/cac:AgentParty"
                 priority="1006"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-06 : Si l’identifiant global de l'agent d'acheteur (EXT-FR-FE-06) est renseigné, alors son schéma (EXT-FR-FE-07) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-06-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-06 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé de l'agent d'acheteur (EXT-FR-FE-06). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-06-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:PaymentMeans/cac:PaymentMandate/cac:PayerParty"
                 priority="1005"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-46 : Si l’identifiant global du payeur (EXT-FR-FE-46) est renseigné, alors son schéma (EXT-FR-FE-47) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-46-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-46 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé du payeur (EXT-FR-FE-46). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-46-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AccountingSupplierParty/cac:Party/cac:AgentParty"
                 priority="1004"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-69 : Si l’identifiant global de l'agent du vendeur (EXT-FR-FE-69) est renseigné, alors son schéma (EXT-FR-FE-70) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-69-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-69 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé de l'agent du vendeur (EXT-FR-FE-69). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-69-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AccountingCustomerParty/cac:Party/cac:ServiceProviderParty/cac:Party"
                 priority="1003"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-92 : Si l’identifiant global du facturé à (EXT-FR-FE-92) est renseigné, alors son schéma (EXT-FR-FE-92-1) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-92-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-92 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé du facturé à (EXT-FR-FE-92). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-92-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:AccountingSupplierParty/cac:Party/cac:ServiceProviderParty/cac:Party"
                 priority="1002"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cac:PartyIdentification/cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-115 : Si l’identifiant global du facturant (EXT-FR-FE-115) est renseigné, alors son schéma (EXT-FR-FE-116) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-115-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cac:PartyIdentification/cbc:ID/@schemeID)) = count(cac:PartyIdentification/cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-115 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé du facturant (EXT-FR-FE-115). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-115-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:Delivery/cac:DeliveryLocation | cn:CreditNote/cac:Delivery/cac:DeliveryLocation"
                 priority="1001"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-71 : Si l’identifiant global du livré à (BT-71) est renseigné, alors son schéma (BT-71-1) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-71-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cbc:ID/@schemeID)) = count(cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/BT-71 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé du livré à (BT-71). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_BT-71-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:Delivery/cac:DeliveryLocation | cn:CreditNote/cac:CreditNoteLine/cac:Delivery/cac:DeliveryLocation"
                 priority="1000"
                 mode="M54">

		<!--ASSERT -->
      <xsl:choose>
         <xsl:when test="empty(cbc:ID[not(@schemeID)])"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-146 : Si l’identifiant global du livré à à la ligne (EXT-FR-FE-146 ) est renseigné, alors son schéma (EXT-FR-FE-147) doit également être renseigné. </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-146-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="count(distinct-values(cbc:ID/@schemeID)) = count(cbc:ID/@schemeID)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-10/EXT-FR-FE-146 : Chaque schemeID ne peut apparaître qu’une seule fois ans l'identifiant privé du livré à à la ligne (EXT-FR-FE-146 ). </xsl:text>
               <xsl:text>
ID:BR-FR-CO-10_EXT-FR-FE-146-2</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M54"/>
   <xsl:template match="@*|node()" priority="-2" mode="M54">
      <xsl:apply-templates select="@*|*" mode="M54"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-12BR-FR-CO-12 — Contrôle des devises et du montant de TVA en comptabilité si la facture n’est pas en EUR-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M55">
      <xsl:variable name="invoiceCurrency" select="cbc:DocumentCurrencyCode"/>
      <xsl:variable name="accountingCurrency" select="cbc:TaxCurrencyCode"/>
      <xsl:variable name="taxAmountValueEUR"
                    select="cac:TaxTotal/cbc:TaxAmount[@currencyID='EUR']"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($invoiceCurrency != 'EUR') or ($accountingCurrency = 'EUR' and string($taxAmountValueEUR))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-12/BT-5 : Si la devise de facture (BT-5) est différente de EUR, alors : - la devise de comptabilité (BT-6) doit être présente et égale à EUR, - le montant de TVA en devise de comptabilité (BT-111) doit être renseigné, - et sa devise (BT-111-1) doit être égale à EUR. Valeurs actuelles : BT-5="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$invoiceCurrency"/>
               <xsl:text/>
               <xsl:text>", BT-6="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$accountingCurrency"/>
               <xsl:text/>
               <xsl:text>", BT-111="</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$taxAmountValueEUR"/>
               <xsl:text/>
               <xsl:text>"/&gt;". </xsl:text>
               <xsl:text>
ID:BR-FR-CO-12_BT-5</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M55"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M55"/>
   <xsl:template match="@*|node()" priority="-2" mode="M55">
      <xsl:apply-templates select="@*|*" mode="M55"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-14BR-FR-CO-14 — Vérification de la note TXD pour les vendeurs membres d’un assujetti unique-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M56">
      <xsl:variable name="isAU"
                    select="exists(cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID = '0231'])"/>
      <xsl:variable name="allNotes"
                    select="string-join(./cbc:Note, '')[contains(., '#TXD#')]"/>
      <xsl:variable name="afterTXD" select="substring-after($allNotes, '#TXD#')"/>
      <xsl:variable name="ValeurTXD"
                    select="if (contains($afterTXD, '#')) then substring-before($afterTXD, '#') else $afterTXD"/>
      <xsl:variable name="hasTXDNote" select="$ValeurTXD='MEMBRE_ASSUJETTI_UNIQUE'"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($isAU) or $hasTXDNote"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-14/BT-29-1 : Si le schéma d’identification du vendeur (BT-29-1) est '0231', cela signifie qu’il est membre d’un assujetti unique. Dans ce cas, une note (BG-1) avec le code sujet 'TXD' (BT-21) et le texte 'MEMBRE_ASSUJETTI_UNIQUE' (BT-22) doit être présente et non "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$ValeurTXD"/>
               <xsl:text/>
               <xsl:text>" </xsl:text>
               <xsl:text>
ID:BR-FR-CO-14_BT-29-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M56"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M56"/>
   <xsl:template match="@*|node()" priority="-2" mode="M56">
      <xsl:apply-templates select="@*|*" mode="M56"/>
   </xsl:template>
   <!--PATTERN BR-FR-CO-15BR-FR-CO-15 — Présence du représentant fiscal si le vendeur est membre d’un assujetti unique (BT-29-1 = 0231)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice | cn:CreditNote" priority="1000" mode="M57">
      <xsl:variable name="isAU"
                    select="exists(cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID = '0231'])"/>
      <xsl:variable name="fiscalRep" select="cac:TaxRepresentativeParty/cac:PartyTaxScheme"/>
      <xsl:variable name="fiscalRepVAT" select="$fiscalRep/cbc:CompanyID"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($isAU) or (exists($fiscalRep) and string($fiscalRepVAT))"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-CO-15/BT-29-1 : Si le vendeur est membre d’un assujetti unique (BT-29-1 = 0231), alors le bloc représentant fiscal (BG-11) doit être présent et contenir le numéro de TVA de l’assujetti unique (BT-63). État actuel : représentant fiscal </xsl:text>
               <xsl:text/>
               <xsl:value-of select="name($fiscalRep)"/>
               <xsl:text/>
               <xsl:text>, numéro de TVA = "</xsl:text>
               <xsl:text/>
               <xsl:value-of select="$fiscalRepVAT"/>
               <xsl:text/>
               <xsl:text>". </xsl:text>
               <xsl:text>
ID:BR-FR-CO-15_BT-29-1</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M57"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M57"/>
   <xsl:template match="@*|node()" priority="-2" mode="M57">
      <xsl:apply-templates select="@*|*" mode="M57"/>
   </xsl:template>
   <!--PATTERN BR-FR-DEC-01BR-FR-DEC-01 — Format des montants numériques (max 19 caractères, 2 décimales, séparateur « . »)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AllowanceCharge/cbc:BaseAmount | cn:CreditNote/cac:AllowanceCharge/cbc:BaseAmount"
                 priority="1016"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-93/BT-100 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-93_BT-100</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:AllowanceCharge/cbc:Amount | cn:CreditNote/cac:AllowanceCharge/cbc:Amount"
                 priority="1015"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-92/BT-99 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-92_BT-99</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:LineExtensionAmount"
                 priority="1014"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-106 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide.Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-106</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:AllowanceTotalAmount"
                 priority="1013"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-107 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-107</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:ChargeTotalAmount"
                 priority="1012"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-108 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-108</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount"
                 priority="1011"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-109 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-109</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cbc:TaxAmount" priority="1010" mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-110 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-110</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cbc:TaxAmount" priority="1009" mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-111 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-111</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"
                 priority="1008"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-112 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-112</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:PrepaidAmount"
                 priority="1007"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-113 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-113</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:PayableRoundingAmount"
                 priority="1006"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-114 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-114</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:LegalMonetaryTotal/cbc:PayableAmount"
                 priority="1005"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-115 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-115</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount"
                 priority="1004"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-116 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-116</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount"
                 priority="1003"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-117 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-117</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cbc:LineExtensionAmount | cn:CreditNote/cac:CreditNoteLine/cbc:LineExtensionAmount"
                 priority="1002"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-131 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-131</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:AllowanceCharge/cbc:Amount | cn:CreditNote/cac:CreditNoteLine/cac:AllowanceCharge/cbc:Amount"
                 priority="1001"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-136/BT-141 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-136_BT-141</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:AllowanceCharge/cbc:BaseAmount | cn:CreditNote/cac:CreditNoteLine/cac:AllowanceCharge/cbc:BaseAmount"
                 priority="1000"
                 mode="M58">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-2($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-01/BT-137/BT-142 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="."/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit comporter au plus 2 décimales, être exprimé avec un point comme séparateur, et ne pas dépasser 19 caractères (hors séparateur). Le signe « - » est autorisé. Veuillez corriger ce montant. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-01_BT-137_BT-142</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M58"/>
   <xsl:template match="@*|node()" priority="-2" mode="M58">
      <xsl:apply-templates select="@*|*" mode="M58"/>
   </xsl:template>
   <!--PATTERN BR-FR-DEC-02BR-FR-DEC-02 — Format des quantités numériques (max 19 caractères, 4 décimales, séparateur « . »)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cbc:InvoicedQuantity | cn:CreditNote/cac:CreditNoteLine/cbc:CreditedQuantity"
                 priority="1001"
                 mode="M59">
      <xsl:variable name="quantity" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-decimal-19-4($quantity)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-02/BT-129 : La quantité « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$quantity"/>
               <xsl:text/>
               <xsl:text> » est invalide. Elle doit : - être un nombre avec au plus 4 décimales (séparateur « . »), - contenir au maximum 19 caractères (hors séparateur), - et peut commencer par un signe « - ». Veuillez corriger cette quantité pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-02_BT-129</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M59"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine | cn:CreditNote/cac:CreditNoteLine"
                 priority="1000"
                 mode="M59">
      <xsl:variable name="quantity" select="normalize-space(cac:Price/cbc:BaseQuantity)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($quantity) or custom:is-valid-decimal-19-4($quantity)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-02/BT-149 : La quantité de base du prix « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$quantity"/>
               <xsl:text/>
               <xsl:text> » est invalide. Elle doit : - être un nombre avec au plus 4 décimales (séparateur « . »), - contenir au maximum 19 caractères (hors séparateur), - et peut commencer par un signe « - ». Veuillez corriger cette quantité pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-02_BT-149</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M59"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M59"/>
   <xsl:template match="@*|node()" priority="-2" mode="M59">
      <xsl:apply-templates select="@*|*" mode="M59"/>
   </xsl:template>
   <!--PATTERN BR-FR-DEC-03BR-FR-DEC-03 — Format des montants positifs (max 19 caractères, 6 décimales, séparateur « . »)-->
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine | cn:CreditNote/cac:CreditNoteLine"
                 priority="1002"
                 mode="M60">
      <xsl:variable name="amount" select="normalize-space(cac:Price/cbc:PriceAmount)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($amount) or custom:is-valid-decimal-19-6-positive($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-03/BT-146 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$amount"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 6 décimales (séparateur « . »), - contenir au maximum 19 caractères (hors séparateur). Veuillez corriger ce montant pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-03_BT-146</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M60"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:Price/cac:AllowanceCharge | cn:CreditNote/cac:CreditNoteLine/cac:Price/cac:AllowanceCharge"
                 priority="1001"
                 mode="M60">
      <xsl:variable name="amount" select="normalize-space(cbc:Amount)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($amount) or custom:is-valid-decimal-19-6-positive($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-03/BT-147 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$amount"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 6 décimales (séparateur « . »), - contenir au maximum 19 caractères (hors séparateur). Veuillez corriger ce montant pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-03_BT-147</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M60"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="ubl:Invoice/cac:InvoiceLine/cac:Price/cac:AllowanceCharge/cbc:BaseAmount | cn:CreditNote/cac:CreditNoteLine/cac:Price/cac:AllowanceCharge/cbc:BaseAmount"
                 priority="1000"
                 mode="M60">
      <xsl:variable name="amount" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="not($amount) or custom:is-valid-decimal-19-6-positive($amount)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-03/BT-148 : Le montant « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$amount"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 6 décimales (séparateur « . »), - contenir au maximum 19 caractères (hors séparateur). Veuillez corriger ce montant pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-03_BT-148</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M60"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M60"/>
   <xsl:template match="@*|node()" priority="-2" mode="M60">
      <xsl:apply-templates select="@*|*" mode="M60"/>
   </xsl:template>
   <!--PATTERN BR-FR-DEC-04BR-FR-DEC-04 — Format des taux de TVA (max 4 caractères, 2 décimales, séparateur « . »)-->
   <!--RULE -->
   <xsl:template match="cac:AllowanceCharge/cac:TaxCategory/cbc:Percent"
                 priority="1002"
                 mode="M61">
      <xsl:variable name="rate" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-percent-4-2-positive($rate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-04/BT-96 ou BT-103 : Le taux de TVA « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$rate"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 2 décimales (séparateur « . »), - contenir au maximum 4 caractères (hors séparateur). Veuillez corriger ce taux pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-04_BT-96_BT-103</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M61"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:Percent"
                 priority="1001"
                 mode="M61">
      <xsl:variable name="rate" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-percent-4-2-positive($rate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-04/BT-119 : Le taux de TVA « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$rate"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 2 décimales (séparateur « . »), - contenir au maximum 4 caractères (hors séparateur). Veuillez corriger ce taux pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-04_BT-119</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M61"/>
   </xsl:template>
   <!--RULE -->
   <xsl:template match="cac:Item/cac:ClassifiedTaxCategory/cbc:Percent"
                 priority="1000"
                 mode="M61">
      <xsl:variable name="rate" select="normalize-space(.)"/>
      <!--ASSERT -->
      <xsl:choose>
         <xsl:when test="custom:is-valid-percent-4-2-positive($rate)"/>
         <xsl:otherwise>
            <xsl:message xmlns:iso="http://purl.oclc.org/dsdl/schematron">
               <xsl:text> BR-FR-DEC-04/BT-152 : Le taux de TVA « </xsl:text>
               <xsl:text/>
               <xsl:value-of select="$rate"/>
               <xsl:text/>
               <xsl:text> » est invalide. Il doit : - être un nombre strictement positif (sans signe « - »), - comporter au plus 2 décimales (séparateur « . »), - contenir au maximum 4 caractères (hors séparateur). Veuillez corriger ce taux pour respecter le format requis. </xsl:text>
               <xsl:text>
ID:BR-FR-DEC-04_BT-152</xsl:text>
            </xsl:message>
         </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@*|*" mode="M61"/>
   </xsl:template>
   <xsl:template match="text()" priority="-1" mode="M61"/>
   <xsl:template match="@*|node()" priority="-2" mode="M61">
      <xsl:apply-templates select="@*|*" mode="M61"/>
   </xsl:template>
</xsl:stylesheet>
