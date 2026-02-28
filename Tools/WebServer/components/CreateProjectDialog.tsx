import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProjectService } from "@/services/ProjectService";
import { Project } from "@/types";
import { Plus } from "lucide-react";

interface CreateProjectDialogProps {
  onProjectCreated: (project: Project) => void;
  trigger?: React.ReactNode;
}

export function CreateProjectDialog({ onProjectCreated, trigger }: CreateProjectDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [sourceLang, setSourceLang] = useState('Japanese');
  const [targetLang, setTargetLang] = useState('Chinese (Simplified)');
  
  const handleCreate = async () => {
    if (!name) return;
    
    // Create with a dummy file for demonstration
    const project = await ProjectService.createProject({
      name,
      sourceLang,
      targetLang,
      files: [
        {
          id: `file_${Date.now()}`,
          name: 'Manual.txt',
          path: '/dummy/path/Manual.txt',
          size: 1024,
          sourceLang,
          targetLang,
          progress: 0,
          status: 'pending',
          lastModified: Date.now()
        },
        {
          id: `file_${Date.now()}_2`,
          name: 'Dialogue.json',
          path: '/dummy/path/Dialogue.json',
          size: 2048,
          sourceLang,
          targetLang,
          progress: 0,
          status: 'pending',
          lastModified: Date.now()
        }
      ]
    });
    
    onProjectCreated(project);
    setOpen(false);
    setName('');
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Create Project
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create Project</DialogTitle>
          <DialogDescription>
            Start a new translation project.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">Name</Label>
            <Input 
              id="name" 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              className="col-span-3" 
              placeholder="My Translation Project"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Source</Label>
            <Select value={sourceLang} onValueChange={setSourceLang}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select source language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Japanese">Japanese</SelectItem>
                <SelectItem value="English">English</SelectItem>
                <SelectItem value="Chinese">Chinese</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Target</Label>
             <Select value={targetLang} onValueChange={setTargetLang}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select target language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Chinese (Simplified)">Chinese (Simplified)</SelectItem>
                <SelectItem value="English">English</SelectItem>
                <SelectItem value="Japanese">Japanese</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" onClick={handleCreate} disabled={!name}>Create Project</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}