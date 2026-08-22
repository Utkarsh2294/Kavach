import React, { useState } from 'react';
import { DollarSign, Network, Hash } from 'lucide-react';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';

export function BlastRadiusPage() {
  const { computeExposure, stats } = useLiveDataContext();

  const [spendCap, setSpendCap] = useState(10000);
  const [maxSubAgents, setMaxSubAgents] = useState(5);
  const [maxDepth, setMaxDepth] = useState(3);
  const [result, setResult] = useState(null);

  const handleCompute = async () => {
    const r = await computeExposure({
      spendCap,
      maxSubAgents,
      maxDelegationDepth: maxDepth,
    });
    setResult(r);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Blast Radius Simulator</h1>
        <p className="text-sm text-muted-foreground mt-1">Model worst-case dollar exposure across the delegation tree</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Simulation Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Proposed Spend Cap ($)</label>
              <Input
                type="number"
                value={spendCap}
                onChange={(e) => setSpendCap(Number(e.target.value))}
                min={0}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Max Sub-Agents per Level</label>
              <Input
                type="number"
                value={maxSubAgents}
                onChange={(e) => setMaxSubAgents(Number(e.target.value))}
                min={1}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Max Delegation Depth</label>
              <Input
                type="number"
                value={maxDepth}
                onChange={(e) => setMaxDepth(Number(e.target.value))}
                min={1}
              />
            </div>
            <Button onClick={handleCompute} className="w-full">Compute</Button>
          </CardContent>
        </Card>

        {result ? (
          <div className="space-y-4">
            <Card>
              <CardContent className="p-5">
                <div className="text-sm text-muted-foreground mb-1">Worst-Case Dollar Exposure</div>
                <div className="text-4xl font-bold text-danger-500">
                  <AnimatedCounter value={result.worstCaseDollarExposure} prefix="$" decimals={0} />
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-3 gap-3">
              <Card>
                <CardContent className="p-4 text-center">
                  <DollarSign className="h-5 w-5 text-primary-500 mx-auto mb-1.5" />
                  <div className="text-xs text-muted-foreground">Root Cap (1 agent)</div>
                  <div className="text-lg font-bold text-foreground mt-0.5">
                    ${result.breakdown.rootCap.toLocaleString()}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Network className="h-5 w-5 text-warning-500 mx-auto mb-1.5" />
                  <div className="text-xs text-muted-foreground">Sub-Agents (per level)</div>
                  <div className="text-lg font-bold text-foreground mt-0.5">
                    {result.breakdown.maxSubAgentsPerLevel}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <Hash className="h-5 w-5 text-success-500 mx-auto mb-1.5" />
                  <div className="text-xs text-muted-foreground">Total Nodes Worst Case</div>
                  <div className="text-lg font-bold text-foreground mt-0.5">
                    {result.breakdown.totalNodesWorstCase}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <Card>
            <CardContent className="p-5 text-center text-muted-foreground py-10">
              Enter parameters and click "Compute" to simulate blast radius
            </CardContent>
          </Card>
        )}
      </div>

      <Separator />

      <Card>
        <CardContent className="p-5">
          <div className="text-sm text-muted-foreground mb-1">Current Fleet Exposure</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-foreground">
              ${stats.maxBlastRadius.toLocaleString()}
            </span>
            <span className="text-xs text-muted-foreground">actual fleet max blast radius</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
