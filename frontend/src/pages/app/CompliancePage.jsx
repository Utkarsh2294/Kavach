import React from 'react';
import { Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const COMPLIANCE_CATEGORIES = [
  {
    category: 'GOVERN',
    description: 'Policies and processes to oversee AI system life cycles',
    subcategories: ['Policy Establishment (GOVERN 1.1)', 'Accountability (GOV 1.2)', 'Training & Culture (GOV 2)'],
  },
  {
    category: 'MAP',
    description: 'Establish the context of the AI system',
    subcategories: ['System Mapping (MAP 1.1)', 'Risk Identification (MAP 2.1)'],
  },
  {
    category: 'MEASURE',
    description: 'Assess & quantify risk',
    subcategories: ['Bias & Accuracy (MEASURE 1.1)', 'Performance Monitoring (MEASURE 3.1)'],
  },
  {
    category: 'MANAGE',
    description: 'Treat and control risk',
    subcategories: ['Incident Response (MANAGE 1.1)', 'Explainability (MANAGE 2.1)'],
  },
];

export function CompliancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">NIST AI RMF Compliance</h1>
        <p className="text-sm text-muted-foreground mt-1">Governance alignment with NIST AI Risk Management Framework</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Shield className="h-4 w-4 text-primary-500" />
            4 categories · 8 subcategories · Aligned to NIST AI RMF 1.0
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {COMPLIANCE_CATEGORIES.map((cat) => (
          <Card key={cat.category}>
            <CardContent className="p-5">
              <div className="flex flex-col sm:grid sm:grid-cols-[140px_1fr] gap-4">
                <div className="flex flex-col gap-2">
                  <Badge variant="outline" className="w-fit text-xs font-bold tracking-wider">
                    {cat.category}
                  </Badge>
                  <p className="text-sm text-muted-foreground">{cat.description}</p>
                </div>
                <div className="flex flex-wrap gap-2 items-center">
                  {cat.subcategories.map((sub) => (
                    <Badge
                      key={sub}
                      variant="secondary"
                      className="text-xs py-1 px-3"
                    >
                      {sub}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}